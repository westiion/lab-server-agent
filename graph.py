import logging
from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.perception import perception_node
from src.nodes.planning import planning_node
from src.nodes.action import action_node

logger = logging.getLogger(__name__)

def error_check_node(state: AgentState):
    errors = state.get("errors", [])
    if errors:
        logger.error(f"--- [Error Check] {len(errors)}개의 문제 감지. 시퀀스 중단 ---")
        return {"next_step": END}

    return {"next_step": state.get("next_step")}

def routing_logic(state: AgentState):
    return state.get("next_step", END)

builder = StateGraph(AgentState)

builder.add_node("perception", perception_node)
builder.add_node("planning", planning_node)
builder.add_node("action", action_node)
builder.add_node("error_check", error_check_node)

builder.add_edge(START, "perception")
builder.add_edge("perception", "error_check")
builder.add_edge("planning", "error_check")
builder.add_edge("action", "error_check")

builder.add_conditional_edges(
    "error_check",
    routing_logic,
    {
        "planning": "planning",
        "action": "action",
        "end": END,
        END: END
    }
)

graph = builder.compile()

