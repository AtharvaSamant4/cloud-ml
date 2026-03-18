import pandas as pd
import json
import subprocess
import sys

THRESHOLD = 0.2


def check_drift():
    df = pd.read_csv("monitoring/predictions_log.csv")

    current_dist = df["prediction"].value_counts(normalize=True).to_dict()

    with open("monitoring/baseline.json", "r") as f:
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

        # 🔥 FIX: use same Python environment
        subprocess.run([sys.executable, "training/train.py"])

        print("\n✅ Model retrained")

    else:
        print("\n✅ No drift")


if __name__ == "__main__":
    check_drift()