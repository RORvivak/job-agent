import os
import httpx
import jwt as pyjwt
from datetime import datetime, timedelta, timezone

_BASE = os.environ.get("RAILS_API_BASE", "http://localhost:3000")
_SECRET = os.environ.get("AGENT_SHARED_SECRET", "change_me")
_TIMEOUT = 10


def _make_jwt() -> str:
    payload = {"exp": datetime.now(timezone.utc) + timedelta(hours=1), "iss": "python-agent"}
    return pyjwt.encode(payload, _SECRET, algorithm="HS256")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_make_jwt()}", "Content-Type": "application/json"}


def _post(path: str, data: dict) -> dict:
    with httpx.Client(base_url=_BASE, timeout=_TIMEOUT) as c:
        r = c.post(path, json=data, headers=_headers())
        r.raise_for_status()
        return r.json()


def _get(path: str) -> dict:
    with httpx.Client(base_url=_BASE, timeout=_TIMEOUT) as c:
        r = c.get(path, headers=_headers())
        r.raise_for_status()
        return r.json()


def check_llm_quota() -> int:
    try:
        data = _get("/api/v1/llm_usage")
        return data.get("remaining", 0)
    except Exception:
        return 0


def increment_llm_usage(count: int = 1) -> None:
    try:
        _post("/api/v1/agent/callback", {"event": "llm_usage", "count": count})
    except Exception:
        pass


def log_step(application_id: int, step: str, status: str, message: str, correlation_id: str = "") -> None:
    try:
        _post("/api/v1/agent/callback", {
            "event": "log",
            "application_id": application_id,
            "correlation_id": correlation_id,
            "step": step,
            "status": status,
            "message": message,
        })
    except Exception:
        pass


def update_application(application_id: int, **fields) -> None:
    try:
        _post("/api/v1/agent/callback", {"event": "status_update", "application_id": application_id, **fields})
    except Exception:
        pass


def upload_resume(application_id: int, file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            filename = os.path.basename(file_path)
            with httpx.Client(base_url=_BASE, timeout=30) as c:
                r = c.post(
                    f"/api/v1/applications/{application_id}/upload_resume",
                    files={"file": (filename, f, "application/pdf")},
                    headers={"Authorization": f"Bearer {_make_jwt()}"},
                )
                r.raise_for_status()
        return True
    except Exception as e:
        return False


def upload_cover_letter(application_id: int, file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            filename = os.path.basename(file_path)
            with httpx.Client(base_url=_BASE, timeout=30) as c:
                r = c.post(
                    f"/api/v1/applications/{application_id}/upload_cover_letter",
                    files={"file": (filename, f, "application/pdf")},
                    headers={"Authorization": f"Bearer {_make_jwt()}"},
                )
                r.raise_for_status()
        return True
    except Exception as e:
        return False


def create_application(user_id: int, job: dict, correlation_id: str) -> int:
    try:
        data = _post("/api/v1/agent/callback", {
            "event": "create_application",
            "user_id": user_id,
            "correlation_id": correlation_id,
            "portal": job.get("portal"),
            "job_url": job.get("job_url"),
            "title": job.get("title"),
            "company": job.get("company"),
            "description": job.get("description", ""),
            "relevance_score": job.get("relevance_score", 0),
        })
        return data.get("application_id", 0)
    except Exception:
        return 0
