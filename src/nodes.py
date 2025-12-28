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
