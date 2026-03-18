import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
import joblib
import mlflow
import mlflow.sklearn
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "credit_default.xls")
BASELINE_PATH = os.path.join(BASE_DIR, "monitoring", "baseline.json")
MODEL_PATH = os.path.join(BASE_DIR, "training", "best_model.joblib")
STAGING_MODEL_PATH = os.path.join(BASE_DIR, "training", "staging_model.joblib")
STAGING_METRICS_PATH = os.path.join(BASE_DIR, "training", "staging_metrics.json")
DB_PATH = os.path.join(BASE_DIR, "mlflow.db")

mlflow.set_tracking_uri(f"sqlite:///{DB_PATH}")
mlflow.set_experiment("credit-default")


def load_data():
    df = pd.read_excel(DATA_PATH, header=1)
    df = df.drop(columns=["ID"])
    df = df.rename(columns={"default payment next month": "target"})
    
    # 🔥 Attempt to securely merge newly verified Ground Truth data natively from Neon Database!
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(DATABASE_URL)
            df_db = pd.read_sql("SELECT * FROM predictions_log WHERE actual_label IS NOT NULL", con=engine)
            
            if not df_db.empty:
                # Strip out server tracking diagnostics logically mapping purely to ML inputs
                df_db = df_db.drop(columns=["id", "timestamp", "prediction"], errors='ignore')
                df_db = df_db.rename(columns={"actual_label": "target"})
                
                # Securely combine the two separated datasets natively expanding the algorithm!
                df = pd.concat([df, df_db], ignore_index=True)
                print(f"🔥 Successfully Merged {len(df_db)} verified Ground-Truth rows from Neon DB!", flush=True)
        except Exception as e:
            print("Failed to merge DB ground truth data:", e, flush=True)

    return df


def train():
    df = load_data()

    # 🔥 Save baseline distribution
    baseline = df["target"].value_counts(normalize=True).to_dict()

    if not os.path.exists(os.path.dirname(BASELINE_PATH)):
        os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)

    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f)

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    param_grid = [
        {"n_estimators": 50, "max_depth": 10},
        {"n_estimators": 100, "max_depth": 10},
        {"n_estimators": 50, "max_depth": 15},
        {"n_estimators": 100, "max_depth": 15},
    ]

    best_f1 = 0
    best_model = None

    for params in param_grid:
        with mlflow.start_run():

            model = RandomForestClassifier(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                class_weight="balanced",
                n_jobs=-1,
                random_state=42
            )

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)

            mlflow.log_params(params)
            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("f1_score", f1)
            mlflow.sklearn.log_model(model, "model")

            if f1 > best_f1:
                best_f1 = f1
                best_model = model

    # 🔥 Save STAGING model (do NOT overwrite production!)
    joblib.dump(best_model, STAGING_MODEL_PATH)
    print("Model isolated at training/staging_model.joblib", flush=True)

    # 🔥 Save metrics for Admin UI dashboard
    staging_metrics = {
        "f1_score": round(best_f1, 4),
        "status": "pending_approval"
    }
    with open(STAGING_METRICS_PATH, "w") as f:
        json.dump(staging_metrics, f)

    print("✅ Staging training complete. Best F1:", best_f1)


if __name__ == "__main__":
    train()