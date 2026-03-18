import os
from functools import lru_cache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
from datetime import datetime

from monitoring.drift_check import check_drift

# 🔥 Base directory resolution for absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "training", "best_model.joblib")
LOG_DIR = os.path.join(BASE_DIR, "monitoring")
LOG_FILE = os.path.join(LOG_DIR, "predictions_log.csv")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@lru_cache()
def load_model():
    """Cache the loaded model in memory so it's only loaded once across requests."""
    return joblib.load(MODEL_PATH)


@app.get("/run-drift")
def run_drift():
    """Triggered by GitHub Actions daily at 2 AM IST"""
    try:
        check_drift()
        
        # 🔥 IMPORTANT: clear cached model after retraining
        try:
            load_model.cache_clear()
        except:
            pass
            
        return {"status": "drift check completed"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/")
def health():
    return {"status": "ok"}


# 🔥 Build full feature vector from minimal inputs
def build_full_input(data):
    return {
        "LIMIT_BAL": data["LIMIT_BAL"],
        "SEX": 2,          
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": data["AGE"], 

        # Replicate repayment behavior
        "PAY_0": data["PAY_0"],
        "PAY_2": data["PAY_0"],
        "PAY_3": data["PAY_0"],
        "PAY_4": data["PAY_0"],
        "PAY_5": data["PAY_0"],
        "PAY_6": data["PAY_0"],

        # Replicate bill amounts
        "BILL_AMT1": data["BILL_AMT1"],
        "BILL_AMT2": data["BILL_AMT1"],
        "BILL_AMT3": data["BILL_AMT1"],
        "BILL_AMT4": data["BILL_AMT1"],
        "BILL_AMT5": data["BILL_AMT1"],
        "BILL_AMT6": data["BILL_AMT1"],

        # Replicate payment amounts
        "PAY_AMT1": data["PAY_AMT1"],
        "PAY_AMT2": data["PAY_AMT1"],
        "PAY_AMT3": data["PAY_AMT1"],
        "PAY_AMT4": data["PAY_AMT1"],
        "PAY_AMT5": data["PAY_AMT1"],
        "PAY_AMT6": data["PAY_AMT1"],
    }


@app.post("/predict")
def predict(data: dict):
    try:
        # 🔥 Load model efficiently using lru_cache
        model = load_model()

        # Build full feature set
        full_data = build_full_input(data)

        df = pd.DataFrame([full_data])

        # Predict
        prediction = model.predict(df)[0]

        # Add logging info
        df["prediction"] = prediction
        df["timestamp"] = datetime.now()

        # Ensure monitoring folder exists
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)

        # ✅ Safe CSV appending (writes headers only if file doesn't exist)
        write_header = not os.path.exists(LOG_FILE)
        df.to_csv(LOG_FILE, mode="a", header=write_header, index=False)

        return {"prediction": int(prediction)}

    except Exception as e:
        return {"error": str(e)}