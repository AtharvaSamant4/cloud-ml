from fastapi import FastAPI
import pandas as pd
import joblib
from datetime import datetime
import os

app = FastAPI()

MODEL_PATH = "training/best_model.joblib"
LOG_FILE = "monitoring/predictions_log.csv"

model = joblib.load(MODEL_PATH)


def load_model():
    global model
    model = joblib.load(MODEL_PATH)


@app.get("/")
def home():
    return {"message": "API running"}


@app.post("/predict")
def predict(data: dict):
    global model

    # 🔥 Reload model every time (simple but effective)
    load_model()

    df = pd.DataFrame([data])
    pred = model.predict(df)[0]

    df["prediction"] = pred
    df["timestamp"] = datetime.now()

    if not os.path.exists("monitoring"):
        os.makedirs("monitoring")

    if not os.path.exists(LOG_FILE):
        df.to_csv(LOG_FILE, index=False)
    else:
        df.to_csv(LOG_FILE, mode="a", header=False, index=False)

    return {"prediction": int(pred)}