from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
from datetime import datetime
import os

app = FastAPI()

# 🔥 MUST HAVE this to allow browser preflight OPTIONS requests!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "training/best_model.joblib"
LOG_FILE = "monitoring/predictions_log.csv"

# Load model initially
model = joblib.load(MODEL_PATH)


def load_model():
    global model
    model = joblib.load(MODEL_PATH)


# 🔥 Build full feature vector from minimal inputs
def build_full_input(data):
    return {
        "LIMIT_BAL": data["LIMIT_BAL"],
        "SEX": 2,          # SEX comes BEFORE AGE in fit()
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": data["AGE"], # AGE must come AFTER MARRIAGE

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


@app.get("/")
def home():
    return {"message": "ML API is running"}


@app.post("/predict")
def predict(data: dict):
    global model

    try:
        # 🔥 Always reload latest model (after retraining)
        load_model()

        # 🔥 Build full feature set
        full_data = build_full_input(data)

        df = pd.DataFrame([full_data])

        # Predict
        prediction = model.predict(df)[0]

        # Add logging info
        df["prediction"] = prediction
        df["timestamp"] = datetime.now()

        # Ensure monitoring folder exists
        if not os.path.exists("monitoring"):
            os.makedirs("monitoring")

        # Save logs
        if not os.path.exists(LOG_FILE):
            df.to_csv(LOG_FILE, index=False)
        else:
            df.to_csv(LOG_FILE, mode="a", header=False, index=False)

        return {"prediction": int(prediction)}

    except Exception as e:
        return {"error": str(e)}