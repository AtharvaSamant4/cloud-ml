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
from sqlalchemy import create_engine, text
from prometheus_fastapi_instrumentator import Instrumentator

from monitoring.drift_check import check_drift

# 🔥 Base directory resolution for absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "training", "best_model.joblib")
STAGING_MODEL_PATH = os.path.join(BASE_DIR, "training", "staging_model.joblib")
STAGING_METRICS_PATH = os.path.join(BASE_DIR, "training", "staging_metrics.json")
DEBUG_LOG_FILE = os.path.join(BASE_DIR, "monitoring", "debug.log")

app = FastAPI()

# 🔥 Expose Prometheus Metrics for Grafana
Instrumentator().instrument(app).expose(app)

# 🔥 Initialize Neon PostgreSQL Database
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

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
            
            print("=== DRIFT CHECK FINISHED (Staging Model Prepared) ===", flush=True)
            
            # Write debug file log
            with open(DEBUG_LOG_FILE, "a") as f:
                f.write(f"STAGING MODEL WAITING AT {time.time()}\n")
            
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


@app.get("/staging-model")
def staging_model():
    if not os.path.exists(STAGING_METRICS_PATH):
        return {"status": "none"}
    with open(STAGING_METRICS_PATH, "r") as f:
        import json
        metrics = json.load(f)
    return {"status": "pending", "metrics": metrics}

@app.post("/approve-model")
def approve_model():
    if not os.path.exists(STAGING_MODEL_PATH):
        return {"error": "no staging model found"}
    
    import shutil
    # Deploy to production natively
    shutil.copy(STAGING_MODEL_PATH, MODEL_PATH)

    if s3 is not None:
        try:
            s3.upload_file(MODEL_PATH, os.environ.get("R2_BUCKET", ""), "best_model.joblib")
        except Exception:
            pass

    load_model.cache_clear()
    os.remove(STAGING_MODEL_PATH)
    if os.path.exists(STAGING_METRICS_PATH):
        os.remove(STAGING_METRICS_PATH)
        
    return {"status": "approved"}

@app.post("/reject-model")
def reject_model():
    if os.path.exists(STAGING_MODEL_PATH):
        os.remove(STAGING_MODEL_PATH)
    if os.path.exists(STAGING_METRICS_PATH):
        os.remove(STAGING_METRICS_PATH)
    return {"status": "rejected"}

@app.get("/unlabeled-predictions")
def get_unlabeled():
    if not engine:
        return {"logs": [], "message": "Database not configured"}
    try:
        df = pd.read_sql(
            'SELECT id, timestamp, prediction, "LIMIT_BAL", "AGE", "PAY_0" FROM predictions_log WHERE actual_label IS NULL ORDER BY timestamp DESC LIMIT 50', 
            con=engine
        )
        if "timestamp" in df.columns:
            df["timestamp"] = df["timestamp"].astype(str)
        logs = df.to_dict(orient="records")
        return {"count": len(logs), "logs": logs}
    except Exception as e:
        return {"logs": [], "message": "Query failed. Did you add the actual_label column in Neon?", "error": str(e)}

@app.post("/update-ground-truth/{row_id}")
def update_truth(row_id: int, actual_label: int):
    if not engine:
        return {"error": "Database not configured"}
    try:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE predictions_log SET actual_label = :label WHERE id = :id"), 
                {"label": actual_label, "id": row_id}
            )
        return {"status": "success", "row_id": row_id, "actual_label": actual_label}
    except Exception as e:
        return {"error": str(e)}

@app.get("/model-info")
def model_info():
    if not os.path.exists(MODEL_PATH):
        return {"error": "model not found"}

    return {
        "model_path": MODEL_PATH,
        "last_modified": os.path.getmtime(MODEL_PATH)
    }


@app.get("/logs")
def get_logs():
    if not engine:
        return {"logs": [], "message": "Database not configured"}

    try:
        # Read identically matching format leveraging UI mapped view
        df = pd.read_sql("SELECT * FROM ui_logs LIMIT 20", con=engine)
        
        # Datetimes fail cleanly translating JSON manually natively over HTTP,
        # Parse timestamp column converting strictly beforehand
        if "timestamp" in df.columns:
            df["timestamp"] = df["timestamp"].astype(str)

        logs = df.to_dict(orient="records")

        return {
            "count": len(logs),
            "logs": logs
        }
    except Exception as e:
        return {"logs": [], "message": "No logs yet or view missing", "error": str(e)}


@app.delete("/logs")
def clear_logs():
    if engine:
        try:
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM predictions_log"))
        except Exception:
            pass
    return {"status": "logs cleared"}


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

        # ✅ Send pure matrix strictly over Cloud Network
        if engine:
            df.to_sql("predictions_log", con=engine, if_exists="append", index=False)

        return {"prediction": int(prediction)}

    except Exception as e:
        return {"error": str(e)}