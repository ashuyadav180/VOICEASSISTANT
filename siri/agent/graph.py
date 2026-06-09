"""LangGraph state machine for multi-step agent tasks."""

from __future__ import annotations

import logging
from typing import Any, TypedDict

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class AgentGraphState(TypedDict):
    transcript: str
    plan: list[str]
    current_step: int
    tool_results: list[dict]
    response: str
    done: bool


def _plan_step(state: AgentGraphState) -> AgentGraphState:
    transcript = state["transcript"]
    plan = []
    lower = transcript.lower()

    if "search" in lower and "save" in lower:
        plan = ["search_web", "take_note", "speak_result"]
    elif "open" in lower and "code" in lower:
        plan = ["search_files", "open_app", "open_file", "speak_result"]
    elif "email" in lower:
        plan = ["draft_email", "compose_email", "speak_result"]
    else:
        plan = ["execute_intent", "speak_result"]

    return {**state, "plan": plan, "current_step": 0, "tool_results": [], "done": False}


def _execute_step(state: AgentGraphState) -> AgentGraphState:
    step = state["current_step"]
    plan = state["plan"]
    if step >= len(plan):
        return {**state, "done": True}

    current = plan[step]
    results = list(state["tool_results"])
    results.append({"step": current, "status": "executed"})
    next_step = step + 1
    done = next_step >= len(plan)

    return {
        **state,
        "current_step": next_step,
        "tool_results": results,
        "done": done,
        "response": state.get("response", "Task completed."),
    }


def _should_continue(state: AgentGraphState) -> str:
    return "end" if state.get("done") else "execute"


def build_agent_graph():
    if not LANGGRAPH_AVAILABLE:
        logger.warning("langgraph not installed — using simple brain loop")
        return None

    graph = StateGraph(AgentGraphState)
    graph.add_node("plan", _plan_step)
    graph.add_node("execute", _execute_step)
    graph.set_entry_point("plan")
    graph.add_edge("plan", "execute")
    graph.add_conditional_edges("execute", _should_continue, {"execute": "execute", "end": END})
    return graph.compile()


class GraphOrchestrator:
    """Optional LangGraph wrapper for complex multi-step flows."""

    def __init__(self) -> None:
        self.graph = build_agent_graph()

    def run(self, transcript: str) -> dict[str, Any]:
        if not self.graph:
            return {"plan": ["execute_intent"], "response": ""}

        result = self.graph.invoke({
            "transcript": transcript,
            "plan": [],
            "current_step": 0,
            "tool_results": [],
            "response": "",
            "done": False,
        })
        return result
