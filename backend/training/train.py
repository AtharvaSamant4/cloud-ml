import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
import joblib
import mlflow
import mlflow.sklearn
import json

mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("credit-default")


def load_data():
    df = pd.read_excel("data/credit_default.xls", header=1)
    df = df.drop(columns=["ID"])
    df = df.rename(columns={"default payment next month": "target"})
    return df


def train():
    df = load_data()

    # 🔥 Save baseline distribution
    baseline = df["target"].value_counts(normalize=True).to_dict()

    with open("monitoring/baseline.json", "w") as f:
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

    # 🔥 Save BEST model (overwrite old one)
    joblib.dump(best_model, "training/best_model.joblib")

    print("✅ Training complete. Best F1:", best_f1)


if __name__ == "__main__":
    train()