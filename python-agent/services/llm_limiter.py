import os
from functools import wraps
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from services.rails_client import check_llm_quota, increment_llm_usage

_llm_cache: dict = {}


def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if provider not in _llm_cache:
        if provider == "anthropic":
            _llm_cache[provider] = ChatAnthropic(
                model="claude-sonnet-4-6",
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                max_tokens=4096,
            )
        else:
            _llm_cache[provider] = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=os.environ.get("OPENAI_API_KEY"),
            )
    return _llm_cache[provider]


def llm_guarded(est_calls: int = 1):
    """Decorator: checks quota before node runs, increments after."""
    def decorator(node_fn):
        @wraps(node_fn)
        def wrapped(state: dict) -> dict:
            remaining = check_llm_quota()
            if remaining < est_calls:
                state.setdefault("errors", []).append({
                    "step": node_fn.__name__,
                    "msg": "llm_quota_exceeded",
                    "detail": "Daily LLM API limit reached. Automation stopped.",
                })
                return state
            result = node_fn(state)
            increment_llm_usage(est_calls)
            return result
        return wrapped
    return decorator
