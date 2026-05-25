from langgraph.graph import StateGraph, END

from graph.state import JobAgentState
from graph.nodes import (
    collect_preferences,
    parse_resume,
    search_jobs,
    fetch_jobs,
    rank_jobs,
    select_next_job,
    customize_resume,
    generate_cover_letter,
    save_application,
    error_handler,
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


def _has_more_jobs(state: JobAgentState) -> str:
    return "next" if state.get("ranked_jobs") else "done"


def build_prep_graph(use_remotive: bool = True):
    g = StateGraph(JobAgentState)

    g.add_node("collect_preferences", collect_preferences.run)
    g.add_node("parse_resume", parse_resume.run)
    g.add_node("fetch_jobs", fetch_jobs.run if use_remotive else search_jobs.run)
    g.add_node("rank_jobs", rank_jobs.run)
    g.add_node("select_next_job", select_next_job.run)
    g.add_node("customize_resume", customize_resume.run)
    g.add_node("generate_cover_letter", generate_cover_letter.run)
    g.add_node("save_application", save_application.run)
    g.add_node("error_handler", error_handler.run)

    g.set_entry_point("collect_preferences")
    g.add_edge("collect_preferences", "parse_resume")
    g.add_conditional_edges("parse_resume", _has_quota_error, {"ok": "fetch_jobs", "error": END})
    g.add_edge("fetch_jobs", "rank_jobs")
    g.add_conditional_edges("rank_jobs", _has_ranked_jobs, {"ok": "select_next_job", "error": END, "done": END})
    g.add_edge("select_next_job", "customize_resume")
    g.add_conditional_edges("customize_resume", _has_quota_error, {"ok": "generate_cover_letter", "error": "error_handler"})
    g.add_conditional_edges("generate_cover_letter", _has_quota_error, {"ok": "save_application", "error": "error_handler"})
    g.add_conditional_edges("save_application", _has_more_jobs, {"next": "select_next_job", "done": END})
    g.add_conditional_edges("error_handler", _has_more_jobs, {"next": "select_next_job", "done": END})

    return g.compile()


def build_graph():
    return build_prep_graph(use_remotive=False)
