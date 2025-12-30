import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from src.state import AgentState
from src.config import DB_PATH
from src.nodes import (
    academic_research_node,
    human_review_node,
    refiner_node,
    validator_node,
    web_research_node,
    writer_node,
)



def validation_router(state: AgentState) -> str:
    """
    Determine the next node after validation.

    - If the draft is valid, proceed to human review.
    - If validation fails and revision_count >= 3, proceed to human review to prevent infinite loops.
    - Otherwise, route to the refiner for improvement.
    """
    if state.get("is_valid"):
        return "human_review"

    if state.get("revision_count", 0) >= 3:
        return "human_review"

    return "refiner"


def human_router(state: AgentState) -> str:
    """
    Determine the next step after human review.

    - If the feedback contains the word "approve" (case-insensitive), end the workflow.
    - Otherwise, route to the refiner to address the provided feedback.
    """
    feedback = state.get("feedback", "").lower()
    if "approve" in feedback:
        return END
    return "refiner"


# --- Graph Construction ---
builder = StateGraph(AgentState)

# Register nodes
builder.add_node("web_researcher", web_research_node)
builder.add_node("academic_researcher", academic_research_node)
builder.add_node("writer", writer_node)
builder.add_node("validator", validator_node)
builder.add_node("human_review", human_review_node)
builder.add_node("refiner", refiner_node)

# Define fixed edges (primary sequential flow)
builder.add_edge(START, "web_researcher")
builder.add_edge("web_researcher", "academic_researcher")
builder.add_edge("academic_researcher", "writer")
builder.add_edge("writer", "validator")

# Conditional routing
builder.add_conditional_edges("validator", validation_router)
builder.add_conditional_edges("human_review", human_router)

# Refinement loop
builder.add_edge("refiner", "web_researcher")


def get_graph():
    """
    Compile and return the LangGraph workflow with SQLite checkpointing.

    The graph is configured to:
    - Persist state in the SQLite database specified by DB_PATH.
    - Interrupt execution before the 'human_review' node for Human-in-the-Loop interaction.

    Returns:
        The compiled graph instance ready for execution.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    memory = SqliteSaver(conn)

    return builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review"],
    )