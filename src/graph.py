import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END, START

from src.state import AgentState
from src.config import DB_PATH

from src.nodes import (
    web_research_node, 
    academic_research_node, 
    writer_node, 
    validator_node, 
    human_review_node, 
    refiner_node
)



#Routers

def validation_router(state: AgentState):
    if state.get("is_valid") is True:
        return "human_review"
    
    
    if state.get("revision_count", 0) >= 2:
        return "human_review" 
        
    return "web_researcher"

def human_router(state: AgentState):
    feedback = state.get("feedback", "").lower()
    
    if "approve" in feedback:
        return END
    

    return "refiner"



builder = StateGraph(AgentState)

# Add Nodes
builder.add_node("web_researcher", web_research_node)
builder.add_node("academic_researcher", academic_research_node)
builder.add_node("writer", writer_node)
builder.add_node("validator", validator_node)
builder.add_node("human_review", human_review_node)
builder.add_node("refiner", refiner_node)

# Parallel Branching (Fan-out)
# Both nodes start at the same time
builder.add_edge(START, "web_researcher")
builder.add_edge(START, "academic_researcher")

# Joining (Fan-in)
# Writer starts ONLY after BOTH researchers finish
builder.add_edge("web_researcher", "writer")
builder.add_edge("academic_researcher", "writer")

# Standard Loop Logic
builder.add_edge("writer", "validator")
builder.add_conditional_edges("validator", validation_router)
builder.add_conditional_edges("human_review", human_router)
builder.add_edge("refiner", "web_researcher") # Loop back to research/search
builder.add_edge("refiner", "academic_researcher")


# Compile_graph
def get_graph():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    memory = SqliteSaver(conn)
    return builder.compile(checkpointer=memory, interrupt_before=["human_review"])
