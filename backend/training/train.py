import os
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "credit_default.xls")
BASELINE_PATH = os.path.join(BASE_DIR, "monitoring", "baseline.json")
STAGING_MODEL_PATH = os.path.join(BASE_DIR, "training", "staging_model.joblib")
STAGING_METRICS_PATH = os.path.join(BASE_DIR, "training", "staging_metrics.json")

# Max rows to train on — keeps memory under ~512MB on Render free tier
SAMPLE_SIZE = 5000


def load_data():
    df = pd.read_excel(DATA_PATH, header=1)
    df = df.drop(columns=["ID"])
    df = df.rename(columns={"default payment next month": "target"})

    # Optionally merge verified ground-truth labels from PostgreSQL
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(DATABASE_URL)
            df_db = pd.read_sql(
                "SELECT * FROM predictions_log WHERE actual_label IS NOT NULL",
                con=engine
            )
            if not df_db.empty:
                df_db = df_db.drop(columns=["id", "timestamp", "prediction"], errors="ignore")
                df_db = df_db.rename(columns={"actual_label": "target"})
                df = pd.concat([df, df_db], ignore_index=True)
                print(f"Merged {len(df_db)} ground-truth rows from DB.", flush=True)
        except Exception as e:
            print(f"Skipping DB ground-truth merge: {e}", flush=True)

    # Sample to cap memory usage
    if len(df) > SAMPLE_SIZE:
        df = df.sample(SAMPLE_SIZE, random_state=42)
        print(f"Sampled dataset to {SAMPLE_SIZE} rows.", flush=True)

    return df


def train():
    df = load_data()

    # Save baseline class distribution for drift detection
    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    baseline = df["target"].value_counts(normalize=True).to_dict()
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f)

    X = df.drop("target", axis=1)
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Lightweight param grid — tuned for low-memory environments
    param_grid = [
        {"n_estimators": 20, "max_depth": 5},
        {"n_estimators": 20, "max_depth": 6},
    ]

    best_f1 = 0
    best_model = None

    for params in param_grid:
        print(f"Training: {params}", flush=True)
        model = RandomForestClassifier(
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            class_weight="balanced",
            n_jobs=1,  # single job to avoid memory spikes
            random_state=42
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        print(f"  accuracy={acc:.4f}  f1={f1:.4f}", flush=True)

        if f1 > best_f1:
            best_f1 = f1
            best_model = model

    # Save staging model — does NOT overwrite production
    joblib.dump(best_model, STAGING_MODEL_PATH)
    print("Staging model saved to training/staging_model.joblib", flush=True)

    # Save metrics for Admin UI approval panel
    with open(STAGING_METRICS_PATH, "w") as f:
        json.dump({"f1_score": round(best_f1, 4), "status": "pending_approval"}, f)

    print(f"Training complete. Best F1: {best_f1:.4f}", flush=True)


if __name__ == "__main__":
    train()
