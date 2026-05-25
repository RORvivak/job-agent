from typing import TypedDict, Optional, Any


class JobAgentState(TypedDict, total=False):
    user_id: int
    correlation_id: str
    application_id: Optional[int]
    preference_ids: Optional[list[int]]
    preferences: dict[str, Any]
    resume_path: Optional[str]
    parsed_resume: Optional[dict]
    jobs: list[dict]
    ranked_jobs: list[dict]
    current_job: Optional[dict]
    customized_resume_path: Optional[str]
    cover_letter_path: Optional[str]
    errors: list[dict]
    step_log: list[dict]
    run_type: str  # "run_prep" | "run_automation"
