from langgraph.graph import StateGraph, END

from graph.state import JobAgentState
from graph.nodes import (
    collect_preferences,
    parse_resume,
    search_jobs,
    rank_jobs,
    select_next_job,
    customize_resume,
    generate_cover_letter,
    apply_job,
    external_portal_handler,
    save_application,
    error_handler,
    retry_failed_application,
)


def _has_quota_error(state: JobAgentState) -> str:
    for e in state.get("errors", []):
        if e.get("msg") == "llm_quota_exceeded":
            return "error"
    return "ok"


def _has_ranked_jobs(state: JobAgentState) -> str:
    for e in state.get("errors", []):
        if e.get("msg") == "llm_quota_exceeded":
            return "error"
    return "ok" if state.get("ranked_jobs") else "done"


def _route_after_apply(state: JobAgentState) -> str:
    result = state.get("apply_result", {})
    errors = state.get("errors", [])
    if errors:
        return "error"
    if result.get("external_url"):
        return "external"
    if result.get("success"):
        return "save"
    return "error"


def _route_after_external(state: JobAgentState) -> str:
    result = state.get("apply_result", {})
    if result.get("success"):
        return "save"
    return "error"


def _has_more_jobs(state: JobAgentState) -> str:
    return "next" if state.get("ranked_jobs") else "done"


def build_graph():
    g = StateGraph(JobAgentState)

    g.add_node("collect_preferences", collect_preferences.run)
    g.add_node("parse_resume", parse_resume.run)
    g.add_node("search_jobs", search_jobs.run)
    g.add_node("rank_jobs", rank_jobs.run)
    g.add_node("select_next_job", select_next_job.run)
    g.add_node("customize_resume", customize_resume.run)
    g.add_node("generate_cover_letter", generate_cover_letter.run)
    g.add_node("apply_job", apply_job.run)
    g.add_node("external_portal_handler", external_portal_handler.run)
    g.add_node("save_application", save_application.run)
    g.add_node("error_handler", error_handler.run)

    g.set_entry_point("collect_preferences")
    g.add_edge("collect_preferences", "parse_resume")
    g.add_conditional_edges("parse_resume", _has_quota_error, {"ok": "search_jobs", "error": END})
    g.add_edge("search_jobs", "rank_jobs")
    g.add_conditional_edges("rank_jobs", _has_ranked_jobs, {"ok": "select_next_job", "error": END, "done": END})
    g.add_edge("select_next_job", "customize_resume")
    g.add_edge("customize_resume", "generate_cover_letter")
    g.add_conditional_edges("generate_cover_letter", _has_quota_error, {"ok": "apply_job", "error": END})
    g.add_conditional_edges("apply_job", _route_after_apply, {
        "save": "save_application",
        "external": "external_portal_handler",
        "error": "error_handler",
    })
    g.add_conditional_edges("external_portal_handler", _route_after_external, {
        "save": "save_application",
        "error": "error_handler",
    })
    g.add_conditional_edges("save_application", _has_more_jobs, {
        "next": "select_next_job",
        "done": END,
    })
    g.add_conditional_edges("error_handler", _has_more_jobs, {
        "next": "select_next_job",
        "done": END,
    })

    return g.compile()


def build_retry_graph():
    g = StateGraph(JobAgentState)

    g.add_node("retry_failed_application", retry_failed_application.run)
    g.add_node("select_next_job", select_next_job.run)
    g.add_node("customize_resume", customize_resume.run)
    g.add_node("generate_cover_letter", generate_cover_letter.run)
    g.add_node("apply_job", apply_job.run)
    g.add_node("external_portal_handler", external_portal_handler.run)
    g.add_node("save_application", save_application.run)
    g.add_node("error_handler", error_handler.run)

    g.set_entry_point("retry_failed_application")
    g.add_edge("retry_failed_application", "select_next_job")
    g.add_edge("select_next_job", "customize_resume")
    g.add_edge("customize_resume", "generate_cover_letter")
    g.add_edge("generate_cover_letter", "apply_job")
    g.add_conditional_edges("apply_job", _route_after_apply, {
        "save": "save_application",
        "external": "external_portal_handler",
        "error": "error_handler",
    })
    g.add_conditional_edges("external_portal_handler", _route_after_external, {
        "save": "save_application",
        "error": "error_handler",
    })
    g.add_edge("save_application", END)
    g.add_edge("error_handler", END)

    return g.compile()
