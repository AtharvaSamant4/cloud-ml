# Cloud ML Pipeline with Monitoring & Retraining

## Overview

This project implements an end-to-end Machine Learning system with:

* Model training and experiment tracking
* API-based inference
* Prediction logging
* Drift detection
* Automated retraining

The system is designed to simulate a real-world ML lifecycle on cloud infrastructure.

---

## Architecture

```
User → FastAPI → Model → Prediction
                    ↓
                Logging
                    ↓
            Drift Detection
                    ↓
              Retraining
                    ↓
           Updated Model
```

---

## Features

* RandomForest model for credit default prediction
* MLflow for experiment tracking
* FastAPI for serving predictions
* Logging of all incoming predictions
* Drift detection based on distribution shift
* Automatic retraining using new data

---

## Project Structure

```
training/      → model training
serving/       → API (FastAPI)
monitoring/    → drift detection & logs
features/      → feature processing
```

---

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Train model

```
python training/train.py
```

### 3. Run API

```
uvicorn serving.api:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## Monitoring & Retraining

### Run drift check

```
python monitoring/drift_check.py
```

If drift is detected:

* Model is retrained automatically
* New model replaces old one

---

## Notes

* Retraining uses logged predictions as pseudo-labels (simulation)
* In real systems, labels come from actual outcomes

---

## Future Improvements

* Use real feedback labels
* Automate retraining via scheduler (cron)
* Deploy fully on cloud (EC2, S3, etc.)

---

## Summary

This project demonstrates a complete ML system that:

* serves predictions
* monitors data drift
* retrains automatically

Designed to reflect real-world ML deployment practices.
