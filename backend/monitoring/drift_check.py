import pandas as pd
import json
import subprocess
import sys
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_FILE = os.path.join(BASE_DIR, "monitoring", "baseline.json")
TRAIN_SCRIPT = os.path.join(BASE_DIR, "training", "train.py")

THRESHOLD = 0.05


def check_drift():
    print("Running drift check...", flush=True)

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL or not os.path.exists(BASELINE_FILE):
        print("Not enough data for drift detection (Missing DB or Baseline)", flush=True)
        return

    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql("SELECT prediction FROM predictions_log", con=engine)
    except Exception as e:
        print(f"Failed to read from database: {e}", flush=True)
        return

    if df.empty or len(df) < 50:
        print("Not enough data for drift detection", flush=True)
        return

    current_dist = df["prediction"].value_counts(normalize=True).to_dict()

    # Load baseline
    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    current_default = current_dist.get(1, 0)
    baseline_default = baseline.get("1", baseline.get(1, 0))

    drift = abs(current_default - baseline_default)

    print("\n=== DRIFT CHECK ===", flush=True)
    print("Baseline:", baseline_default, flush=True)
    print("Current:", current_default, flush=True)
    print(f"Drift value: {drift}", flush=True)

    if drift > THRESHOLD:
        print("Drift detected → retraining", flush=True)

        # 🔥 FIX: use same Python environment and absolute path
        subprocess.run([sys.executable, TRAIN_SCRIPT])

        print("Retraining complete", flush=True)

    else:
        print("\n✅ No drift", flush=True)


if __name__ == "__main__":
    check_drift()