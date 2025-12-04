import json
import logging
import os
import subprocess
import time
import urllib.request
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

ROUTER_URL = os.getenv("ROUTER_URL", "http://game_router:7000")
POLL_SECONDS = int(os.getenv("AUTOSCALER_POLL_SECONDS", "10"))
MAX_WORKERS = int(os.getenv("AUTOSCALER_MAX_WORKERS", "100"))
MIN_WORKERS = int(os.getenv("AUTOSCALER_MIN_WORKERS", "1"))
SCALE_SERVICE = os.getenv("AUTOSCALER_SERVICE", "game_server")
SCALE_STEP = int(os.getenv("AUTOSCALER_SCALE_STEP", "1"))
COMPOSE_FILE = os.getenv("COMPOSE_FILE_PATH", "/workspace/docker-compose.yaml")


def fetch_status() -> Dict:
    url = f"{ROUTER_URL.rstrip('/')}/status"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_scale(count: int):
    # Shell out to docker compose (v2 plugin). Requires docker socket mounted and compose file available.
    cmd = [
        "docker",
        "compose",
        "-f",
        COMPOSE_FILE,
        "up",
        "--no-recreate",
        "--scale",
        f"{SCALE_SERVICE}={count}",
        "-d",
    ]
    logging.info("Scaling command: %s", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Scaling command failed: %s", exc)


def current_worker_count(status: Dict) -> int:
    return max(len(status.get("workers", {})), MIN_WORKERS)


def total_available_slots(status: Dict) -> int:
    total = 0
    for worker in status.get("workers", {}).values():
        total += int(worker.get("available_slots", 0))
    return total


def total_capacity(status: Dict) -> int:
    total = 0
    for worker in status.get("workers", {}).values():
        total += int(worker.get("capacity", 0))
    return total


def decide_scale(status: Dict) -> int:
    workers = current_worker_count(status)
    available = total_available_slots(status)
    capacity = total_capacity(status)
    games = len(status.get("games", {}))

    # If no capacity left, scale up
    if available == 0 and workers < MAX_WORKERS:
        return min(MAX_WORKERS, workers + SCALE_STEP)

    # If most capacity is idle, scale down cautiously
    if capacity > 0 and available >= capacity - 1 and workers > MIN_WORKERS:
        return max(MIN_WORKERS, workers - SCALE_STEP)

    return workers


def main():
    logging.info(
        "Autoscaler watching %s every %ss (min=%s, max=%s, step=%s)",
        ROUTER_URL,
        POLL_SECONDS,
        MIN_WORKERS,
        MAX_WORKERS,
        SCALE_STEP,
    )
    while True:
        try:
            status = fetch_status()
            desired = decide_scale(status)
            current = current_worker_count(status)

            if desired != current:
                logging.info("Scaling from %s -> %s workers (games=%s)", current, desired, len(status.get("games", {})))
                run_scale(desired)
            else:
                logging.debug("No scaling action required (workers=%s)", current)
        except Exception as exc:
            logging.warning("Autoscaler loop error: %s", exc)

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
