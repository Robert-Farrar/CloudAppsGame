import json
import logging
import os
import random
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_CAPACITY = 5


class WorkerState:
    """Represents a worker container and the games it is hosting."""

    def __init__(self, worker_id: str, host: str, port: int, capacity: int = DEFAULT_CAPACITY):
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.capacity = capacity
        self.games = set()
        self.last_heartbeat = time.time()

    @property
    def available_slots(self) -> int:
        return self.capacity - len(self.games)

    def to_dict(self) -> Dict:
        return {
            "worker_id": self.worker_id,
            "host": self.host,
            "port": self.port,
            "capacity": self.capacity,
            "games": list(self.games),
            "available_slots": self.available_slots,
            "last_heartbeat": self.last_heartbeat,
        }


class RouterState:
    """In-memory registry for workers and game placements."""

    def __init__(self):
        self._lock = threading.Lock()
        self.workers: Dict[str, WorkerState] = {}
        self.game_index: Dict[str, str] = {}
        self.open_game_id: Optional[str] = None
        self.started_games: set[str] = set()

    def _pick_worker(self, available_workers):
        """Pick a worker preferring lowest load; break ties randomly to avoid always choosing the first."""
        if not available_workers:
            return None
        min_games = min(len(w.games) for w in available_workers)
        candidates = [w for w in available_workers if len(w.games) == min_games]
        return random.choice(candidates)

    def register_worker(self, worker_id: str, host: str, port: int, capacity: int = DEFAULT_CAPACITY) -> WorkerState:
        with self._lock:
            state = self.workers.get(worker_id)
            if state:
                state.host = host
                state.port = port
                state.capacity = capacity
                logging.info("Updated worker %s registration", worker_id)
            else:
                state = WorkerState(worker_id, host, port, capacity)
                self.workers[worker_id] = state
                logging.info("Registered worker %s", worker_id)
            state.last_heartbeat = time.time()
            return state

    def heartbeat(self, worker_id: str) -> Optional[WorkerState]:
        with self._lock:
            worker = self.workers.get(worker_id)
            if worker:
                worker.last_heartbeat = time.time()
            return worker

    def allocate_game(self, game_id: str) -> Optional[WorkerState]:
        with self._lock:
            if game_id in self.game_index:
                worker_id = self.game_index[game_id]
                logging.info("Game %s already assigned to worker %s", game_id, worker_id)
                return self.workers.get(worker_id)

            available_workers = [w for w in self.workers.values() if w.available_slots > 0]
            if not available_workers:
                return None

            worker = self._pick_worker(available_workers)
            worker.games.add(game_id)
            self.game_index[game_id] = worker.worker_id
            worker.last_heartbeat = time.time()
            logging.info("Assigned game %s to worker %s", game_id, worker.worker_id)
            return worker

    def allocate_open_game(self, retries: int = 10, delay: float = 0.5) -> Optional[Dict]:
        """
        Return the current open game allocation or create one if none exists.
        If no capacity is available, retry a few times before giving up.
        """
        for _ in range(max(1, retries)):
            with self._lock:
                if self.open_game_id and self.open_game_id in self.game_index and self.open_game_id not in self.started_games:
                    worker_id = self.game_index[self.open_game_id]
                    worker = self.workers.get(worker_id)
                    if worker:
                        return {
                            "game_id": self.open_game_id,
                            "worker": {"worker_id": worker.worker_id, "host": worker.host, "port": worker.port},
                        }

                available_workers = [w for w in self.workers.values() if w.available_slots > 0]
                if available_workers:
                    game_id = str(uuid.uuid4())
                    worker = self._pick_worker(available_workers)
                    worker.games.add(game_id)
                    self.game_index[game_id] = worker.worker_id
                    self.open_game_id = game_id
                    worker.last_heartbeat = time.time()
                    logging.info("Created open game %s on worker %s", game_id, worker.worker_id)
                    return {
                        "game_id": game_id,
                        "worker": {"worker_id": worker.worker_id, "host": worker.host, "port": worker.port},
                    }
            time.sleep(delay)
        return None

    def mark_game_started(self, game_id: str):
        with self._lock:
            self.started_games.add(game_id)
            if self.open_game_id == game_id:
                self.open_game_id = None

    def release_game(self, game_id: str) -> bool:
        with self._lock:
            worker_id = self.game_index.pop(game_id, None)
            if not worker_id:
                return False

            worker = self.workers.get(worker_id)
            if worker and game_id in worker.games:
                worker.games.remove(game_id)
                worker.last_heartbeat = time.time()
                logging.info("Released game %s from worker %s", game_id, worker_id)
                return True
            return False

    def summary(self) -> Dict:
        with self._lock:
            return {
                "workers": {worker_id: worker.to_dict() for worker_id, worker in self.workers.items()},
                "games": dict(self.game_index),
                "open_game_id": self.open_game_id,
                "started_games": list(self.started_games),
            }


ROUTER_STATE = RouterState()


class RouterHandler(BaseHTTPRequestHandler):
    """Simple JSON-based HTTP router for worker/game coordination."""

    def do_GET(self):
        if self.path == "/status":
            self._respond_json(200, ROUTER_STATE.summary())
        else:
            self._respond_json(404, {"error": "Not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._respond_json(400, {"error": "Invalid JSON payload"})
            return

        if self.path == "/workers/register":
            self._handle_register(payload)
        elif self.path == "/workers/heartbeat":
            self._handle_heartbeat(payload)
        elif self.path == "/games/open":
            self._handle_open_game()
        elif self.path == "/games/allocate":
            self._handle_allocate(payload)
        elif self.path == "/games/start":
            self._handle_game_start(payload)
        elif self.path == "/games/release":
            self._handle_release(payload)
        else:
            self._respond_json(404, {"error": "Not found"})

    def _handle_register(self, payload: Dict):
        worker_id = str(payload.get("worker_id") or "")
        host = payload.get("host")
        port = payload.get("port")
        capacity = int(payload.get("capacity", DEFAULT_CAPACITY))

        if not worker_id or not host or port is None:
            self._respond_json(400, {"error": "worker_id, host, and port are required"})
            return

        worker = ROUTER_STATE.register_worker(worker_id, host, int(port), capacity)
        self._respond_json(200, {"worker": worker.to_dict()})

    def _handle_heartbeat(self, payload: Dict):
        worker_id = str(payload.get("worker_id") or "")
        worker = ROUTER_STATE.heartbeat(worker_id)
        if not worker:
            self._respond_json(404, {"error": "Unknown worker"})
            return
        self._respond_json(200, {"worker": worker.to_dict()})

    def _handle_allocate(self, payload: Dict):
        game_id = str(payload.get("game_id") or "")
        if not game_id:
            self._respond_json(400, {"error": "game_id is required"})
            return

        worker = ROUTER_STATE.allocate_game(game_id)
        if not worker:
            self._respond_json(503, {"error": "No workers available"})
            return

        self._respond_json(
            200,
            {
                "game_id": game_id,
                "worker": {
                    "worker_id": worker.worker_id,
                    "host": worker.host,
                    "port": worker.port,
                },
            },
        )

    def _handle_open_game(self):
        allocation = ROUTER_STATE.allocate_open_game()
        if not allocation:
            self._respond_json(503, {"error": "No workers available"})
            return
        self._respond_json(200, allocation)

    def _handle_game_start(self, payload: Dict):
        game_id = str(payload.get("game_id") or "")
        if not game_id:
            self._respond_json(400, {"error": "game_id is required"})
            return
        ROUTER_STATE.mark_game_started(game_id)
        self._respond_json(200, {"ok": True})

    def _handle_release(self, payload: Dict):
        game_id = str(payload.get("game_id") or "")
        if not game_id:
            self._respond_json(400, {"error": "game_id is required"})
            return

        released = ROUTER_STATE.release_game(game_id)
        if not released:
            self._respond_json(404, {"error": "Game not registered"})
            return

        self._respond_json(200, {"released": game_id})

    def _respond_json(self, status_code: int, payload: Dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logging.info("%s - %s", self.address_string(), fmt % args)


def run():
    port = int(os.getenv("ROUTER_PORT", "7000"))
    host = os.getenv("ROUTER_HOST", "0.0.0.0")
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, RouterHandler)
    logging.info("Starting router on %s:%s", host, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Router shutting down.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run()
