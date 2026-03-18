import os
import threading
import time
import sys
import boto3
from functools import lru_cache
from dotenv import load_dotenv

sys.stdout.flush()
load_dotenv()
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
DEBUG_LOG_FILE = os.path.join(LOG_DIR, "debug.log")

app = FastAPI()

if not all([
    os.environ.get("R2_ACCESS_KEY"),
    os.environ.get("R2_SECRET_KEY"),
    os.environ.get("R2_BUCKET"),
    os.environ.get("R2_ENDPOINT")
]):
    print("R2 env variables not set. Running in local fallback mode.", flush=True)
    s3 = None
else:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("R2_SECRET_KEY"),
        endpoint_url=os.environ.get("R2_ENDPOINT")
    )

print("R2 endpoint:", os.environ.get("R2_ENDPOINT"), flush=True)

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
    if not os.path.exists(MODEL_PATH):
        if s3 is not None:
            print("Downloading model from R2...", flush=True)
            try:
                s3.download_file(
                    os.environ.get("R2_BUCKET", ""),
                    "best_model.joblib",
                    MODEL_PATH
                )
            except Exception as e:
                print("Failed to download model:", e, flush=True)
        else:
            print("Skipping R2 operation (no env)", flush=True)

    print("Loading model...", flush=True)
    print("Model loaded from:", MODEL_PATH, flush=True)
    if os.path.exists(MODEL_PATH):
        print("Model last modified:", os.path.getmtime(MODEL_PATH), flush=True)
    return joblib.load(MODEL_PATH)


@app.get("/run-drift")
def run_drift():
    """Triggered by GitHub Actions daily at 2 AM IST, executing freely without blocking the event loop."""
    
    def run():
        try:
            print("=== DRIFT CHECK STARTED ===", flush=True)

            # Small delay to allow Render logging system to attach
            time.sleep(5)

            # Write debug file log
            with open(DEBUG_LOG_FILE, "a") as f:
                f.write(f"DRIFT STARTED AT {time.time()}\n")

            check_drift()
            
            if s3 is not None:
                print("Uploading model to R2...", flush=True)
                try:
                    s3.upload_file(
                        MODEL_PATH,
                        os.environ.get("R2_BUCKET", ""),
                        "best_model.joblib"
                    )
                    print("Model uploaded to R2", flush=True)
                except Exception as e:
                    print("Failed to upload model:", e, flush=True)
            else:
                print("Skipping R2 operation (no env)", flush=True)
            
            # 🔥 IMPORTANT: clear cached model after retraining
            try:
                load_model.cache_clear()
                print("Model cache cleared after retraining", flush=True)
                
                with open(DEBUG_LOG_FILE, "a") as f:
                    f.write(f"MODEL UPDATED AT {time.time()}\n")
            except Exception as e:
                print("Cache clear error:", e, flush=True)
                
            print("=== DRIFT CHECK FINISHED ===", flush=True)
            
            # Write debug file log
            with open(DEBUG_LOG_FILE, "a") as f:
                f.write(f"DRIFT FINISHED AT {time.time()}\n")
            
        except Exception as e:
            print("Drift execution error:", e, flush=True)

    threading.Thread(target=run).start()
    
    return {"status": "drift triggered"}


@app.on_event("startup")
def startup():
    if not os.path.exists(os.path.dirname(MODEL_PATH)):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        
    if s3 is not None:
        try:
            s3.download_file(
                os.environ.get("R2_BUCKET", ""),
                "best_model.joblib",
                MODEL_PATH
            )
            print("Model synced from R2 on startup", flush=True)
        except Exception as e:
            print("No model in R2 yet, using local", flush=True)
    else:
        print("Skipping R2 operation (no env)", flush=True)


@app.get("/debug-log")
def debug_log():
    try:
        with open(DEBUG_LOG_FILE, "r") as f:
            return {"log": f.read()}
    except:
        return {"log": "No logs yet"}


@app.get("/model-info")
def model_info():
    if not os.path.exists(MODEL_PATH):
        return {"error": "model not found"}

    return {
        "model_path": MODEL_PATH,
        "last_modified": os.path.getmtime(MODEL_PATH)
    }


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
        if os.path.exists(MODEL_PATH):
            print("Using model timestamp:", os.path.getmtime(MODEL_PATH), flush=True)

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