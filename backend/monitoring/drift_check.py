import pandas as pd
import json
import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "monitoring", "predictions_log.csv")
BASELINE_FILE = os.path.join(BASE_DIR, "monitoring", "baseline.json")
TRAIN_SCRIPT = os.path.join(BASE_DIR, "training", "train.py")

THRESHOLD = 0.2


def check_drift():
    if not os.path.exists(LOG_FILE) or not os.path.exists(BASELINE_FILE):
        print("Missing log or baseline file. Skipping drift check.")
        return

    df = pd.read_csv(LOG_FILE)

    current_dist = df["prediction"].value_counts(normalize=True).to_dict()

    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    current_default = current_dist.get(1, 0)
    baseline_default = baseline.get("1", baseline.get(1, 0))

    drift = abs(current_default - baseline_default)

    print("\n=== DRIFT CHECK ===")
    print("Baseline:", baseline_default)
    print("Current:", current_default)
    print("Drift:", drift)

    if drift > THRESHOLD:
        print("\n⚠️ DRIFT DETECTED → RETRAINING\n")

        # 🔥 FIX: use same Python environment and absolute path
        subprocess.run([sys.executable, TRAIN_SCRIPT])

        print("\n✅ Model retrained")

    else:
        print("\n✅ No drift")


if __name__ == "__main__":
    check_drift()