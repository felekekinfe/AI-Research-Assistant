from langchain_community.tools import DuckDuckGoSearchRun
from src.config import llm
from src.state import AgentState
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.semantic_scholar import SemanticScholarQueryRun
import logging
import time
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('execution_logs.json')
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)


# Initialize tools
tavily_tool = TavilySearchResults(k=3) 
scholar_tool = SemanticScholarQueryRun()



def web_research_node(state: AgentState) -> dict:
    start_time = time.time()
    query = state.get("refined_query") or state["task"]
    logger.info(json.dumps({"node": "web_researcher", "status": "started", "query": query}))
    
    results = tavily_tool.invoke(query)
    output = {
        "research_data": f"WEB RESULTS:\n{results}\n",
        "messages": [" Gathered deep web insights via Tavily"]
    }
    
    duration = time.time() - start_time
    logger.info(json.dumps({"node": "web_researcher", "status": "completed", "duration": duration, "output_summary": len(output["research_data"])}))
    return output
def academic_research_node(state: AgentState) -> dict:
    """Node 2: Academic Research via Semantic Scholar"""
    query = state.get("refined_query") or state["task"]
    print(f"--- SCHOLAR ACADEMIC RESEARCH: {query} ---")
    
    results = scholar_tool.invoke(query)
    return {
        "research_data": f"ACADEMIC RESULTS:\n{results}\n",
        "messages": ["🎓 Gathered peer-reviewed data via Semantic Scholar"]
    }
def writer_node(state: AgentState) -> dict:
    """
    Writer that synthesizes new data into the existing draft.
    """
    current_draft = state.get("draft", "No draft yet.")
    research_data = state["research_data"]
    task = state["task"]
    feedback = state.get("feedback", "")

    print(f"--- WRITING/REVISING DRAFT ---")

    prompt = f"""
    You are a technical research writer.
    
    Task: {task}
    Current Draft:
    {current_draft}
    
    New Research Data:
    {research_data}
    
    User Feedback (if any):
    {feedback}
    
    INSTRUCTIONS:
    1. Integrate the 'New Research Data' into the 'Current Draft'. 
    2. Do NOT just append it. Rewrite sections if necessary to improve flow.
    3. Ensure the text is cohesive and comprehensive.
    4. If the draft is empty, write a structured initial draft.
    """
    
    new_draft = llm.invoke(prompt).content
    return {"draft": new_draft, "messages": ["✍️  Draft Updated"]}

def validator_node(state: AgentState) -> dict:
    """
    Checks if the draft meets the user's task requirements.
    """
    draft = state["draft"]
    task = state["task"]
    
    prompt = f"""
    Task: {task}
    Draft: {draft}
    
    Is this draft comprehensive and accurate enough to show to the user? 
    Reply strictly with 'PASS' or 'FAIL'.
    """
    response = llm.invoke(prompt).content.upper()
    is_valid = "PASS" in response
    
    return {
        "is_valid": is_valid, 
        "messages": [f"🛡️ Validator: {'Passed' if is_valid else 'Failed - Re-looping'}"]
    }

def human_review_node(state: AgentState):
    """
    Passive node to stop the graph for human input.
    """
    print("--- AWAITING HUMAN INPUT ---")
    return {}

def refiner_node(state: AgentState) -> dict:
    """
    Analyzes feedback to generate a specific fix query.
    """
    feedback = state["feedback"]
    draft = state["draft"]
    
    prompt = f"""
    The user rejected the draft.
    Draft snippet: {draft}...
    User Feedback: {feedback}
    
    What specific search query will solve this problem?
    """
    refined_query = llm.invoke(prompt).content
    
    return {
        "refined_query": refined_query, 
        "messages": [f"🔄 Refiner: Planning search for '{refined_query}'"]
    }