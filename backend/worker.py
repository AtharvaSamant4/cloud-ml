import json
import os
import time
import traceback

import redis

# Import training pipeline (existing logic remains unchanged)
from training.train import train

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QUEUE_KEY = "retrain_jobs"


def get_client():
    return redis.Redis.from_url(REDIS_URL)


def update_status(client: redis.Redis, job_id: str, status: str, message: str | None = None):
    payload = {
        "status": status,
        "updated_at": time.time(),
    }
    if message:
        payload["message"] = message
    client.hset(f"retrain_job:{job_id}", mapping=payload)


def process_job(raw: bytes, client: redis.Redis):
    try:
        job = json.loads(raw)
        job_id = job.get("id", "unknown")
    except Exception:
        print("Received malformed job payload", flush=True)
        return

    print(f"Starting retraining job {job_id}", flush=True)
    update_status(client, job_id, "started")

    try:
        train()
        update_status(client, job_id, "success", "training complete")
        print(f"Job {job_id} finished successfully", flush=True)
    except Exception as e:
        update_status(client, job_id, "failed", str(e))
        print(f"Job {job_id} failed: {e}", flush=True)
        traceback.print_exc()


def main():
    client = get_client()
    print(f"Worker listening on {QUEUE_KEY} (redis={REDIS_URL})", flush=True)
    while True:
        try:
            _, raw = client.brpop(QUEUE_KEY)
            process_job(raw, client)
        except redis.ConnectionError as e:
            print(f"Redis connection error: {e}", flush=True)
            time.sleep(2)
        except Exception as e:
            print(f"Unexpected worker error: {e}", flush=True)
            traceback.print_exc()
            time.sleep(1)


if __name__ == "__main__":
    main()
