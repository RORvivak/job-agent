import os
import json
import signal
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from loguru import logger

from services.redis_client import brpop_queue
from services.rails_client import log_step
from graph.workflow import build_prep_graph, build_graph

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

QUEUE = os.environ.get("JOB_QUEUE_NAME", "job_queue")
MAX_WORKERS = int(os.environ.get("AGENT_MAX_WORKERS", "2"))

_running = True


def handle_shutdown(signum, frame):
    global _running
    logger.info("Shutdown signal received, stopping agent gracefully...")
    _running = False


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


def bootstrap_state(payload: dict) -> dict:
    return {
        "user_id": payload.get("user_id"),
        "correlation_id": payload.get("correlation_id", ""),
        "application_id": payload.get("application_id") or None,
        "preference_ids": payload.get("preference_ids") or None,
        "run_type": payload.get("type", "run_automation"),
        "errors": [],
        "step_log": [],
    }


def run_one(payload: dict) -> None:
    run_type = payload.get("type", "run_automation")
    app_id = payload.get("application_id", 0)
    correlation_id = payload.get("correlation_id", "")
    logger.info(f"Starting {run_type} | correlation_id={correlation_id} | user={payload.get('user_id')}")

    graph = build_prep_graph() if run_type in ("run_prep", "run_automation") else build_graph()
    state = bootstrap_state(payload)

    try:
        final_state = graph.invoke(state, config={"recursion_limit": 200})
        logger.info(f"Completed {run_type} | correlation_id={correlation_id} | steps={len(final_state.get('step_log', []))}")
    except Exception as e:
        logger.exception(f"Fatal error in {run_type} | correlation_id={correlation_id}: {e}")
        if app_id:
            log_step(app_id, "fatal", "error", str(e), correlation_id)


def main():
    logger.info(f"Job Agent starting. Listening on Redis queue: {QUEUE}")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        while _running:
            try:
                payload = brpop_queue(QUEUE, timeout=5)
                if payload is None:
                    continue
                logger.info(f"Received task: type={payload.get('type')} user={payload.get('user_id')}")
                pool.submit(run_one, payload)
            except Exception as e:
                logger.error(f"Queue error: {e}")

    logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
