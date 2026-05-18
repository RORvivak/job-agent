import os
import json
import redis as _redis

_client: _redis.Redis | None = None


def get_redis() -> _redis.Redis:
    global _client
    if _client is None:
        _client = _redis.Redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
        )
    return _client


def brpop_queue(queue: str, timeout: int = 5) -> dict | None:
    r = get_redis()
    result = r.brpop(queue, timeout=timeout)
    if result is None:
        return None
    _, raw = result
    return json.loads(raw)


def publish_progress(correlation_id: str, event: dict) -> None:
    r = get_redis()
    r.publish(f"agent:progress:{correlation_id}", json.dumps(event))
