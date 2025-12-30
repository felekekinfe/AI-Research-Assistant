from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools.semanticscholar.tool import SemanticScholarQueryRun
from src.config import get_llm
from src.state import AgentState

# Initialize search tools
web_search_tool = DuckDuckGoSearchRun()
academic_search_tool = SemanticScholarQueryRun()


def web_research_node(state: AgentState) -> dict:
    """
    Perform web research using DuckDuckGo.

    Retrieves the query from refined_query (if present) or falls back to the original task.
    Appends results to research_data and logs a message.
    """
    query = state.get("refined_query") or state["task"]
    print(f"--- DUCKDUCKGO WEB RESEARCH: {query} ---")

    try:
        results = web_search_tool.run(query)
    except Exception as e:
        results = f"Search failed: {e}"

    return {
        "research_data": f"\n--- WEB RESULTS ({query}) ---\n{results}\n",
        "messages": [f"🌐 Web Search completed: {query}"],
    }



def academic_research_node(state: AgentState) -> dict:
    """
    Perform academic research using Semantic Scholar.

    Handles potential flakiness of the tool with appropriate fallbacks.
    """
    query = state.get("refined_query") or state["task"]
    print(f"--- ACADEMIC RESEARCH: {query} ---")

    try:
        results = academic_search_tool.run(query)
        if not results or "No results found" in results:
            results = "No specific academic papers found."
    except Exception as e:
        print(f"Academic tool error: {e}")
        results = "Academic search unavailable."

    return {
        "research_data": f"\n--- ACADEMIC RESULTS ({query}) ---\n{results}\n",
        "messages": [f"🎓 Academic Search completed: {query}"],
    }



def writer_node(state: AgentState) -> dict:
    """
    Synthesize collected research into a comprehensive draft report.

    Incorporates previous draft and any user feedback for iterative improvement.
    """
    llm = get_llm()
    task = state["task"]
    research_data = state.get("research_data", "")
    current_draft = state.get("draft", "No previous draft.")
    feedback = state.get("feedback", "")

    print("--- WRITING/UPDATING DRAFT ---")

    prompt = f"""
    You are an expert technical writer.

    **Original Task:** {task}

    **Collected Research Data:**
    {research_data}

    **Previous Draft (if any):**
    {current_draft}

    **User Feedback (if any):**
    {feedback}

    **Instructions:**
    1. Produce a comprehensive, well-structured research report in Markdown format (use headers, bullet points, etc.).
    2. Strictly address any provided feedback.
    3. Synthesize information into a cohesive narrative; do not merely append new content.
    4. Cite sources where relevant (e.g., [Source: Web] or [Source: Academic]).
    """

    response = llm.invoke(prompt)

    return {
        "draft": response.content,
        "messages": ["✍️ Draft written/updated"],
    }



def validator_node(state: AgentState) -> dict:
    """
    Validate the quality of the current draft against key criteria.

    Returns a boolean is_valid flag used for conditional routing.
    """
    llm = get_llm()
    task = state["task"]
    draft = state["draft"]

    prompt = f"""
    You are a rigorous Quality Assurance Editor.

    **Task:** {task}
    **Draft (truncated for evaluation):** {draft[:3000]}

    **Evaluation Criteria:**
    1. Does the draft directly and fully address the user's task?
    2. Is the content substantial and non-empty?
    3. Is the draft logically structured and well-organized?

    Respond strictly with "PASS" or "FAIL" only.
    """

    try:
        response = llm.invoke(prompt).content.strip().upper()
        is_valid = "PASS" in response
    except Exception:
        is_valid = True  # Conservative fallback to allow human review

    return {
        "is_valid": is_valid,
        "messages": [f"⚖️ Validator: {'Passed' if is_valid else 'Failed – revision required'}"],
    }



def refiner_node(state: AgentState) -> dict:
    """
    Generate a refined search query when validation fails or feedback is provided.

    Increments revision_count to prevent infinite loops.
    """
    llm = get_llm()
    task = state["task"]
    feedback = state.get("feedback", "Draft failed validation.")

    current_rev = state.get("revision_count", 0)
    new_rev = current_rev + 1

    prompt = f"""
    The current research draft requires improvement.

    **Original Task:** {task}
    **Issue/Feedback:** {feedback}

    Generate one concise, specific search query (different from previous queries) that targets missing information or resolves the identified issue.

    Output only the query string.
    """

    refined_query = llm.invoke(prompt).content.strip().strip('"')

    return {
        "refined_query": refined_query,
        "revision_count": new_rev,
        "messages": [f"🔄 Refiner: Generated new query '{refined_query}' (Revision {new_rev})"],
    }



def human_review_node(state: AgentState) -> dict:
    """
    Placeholder node for human-in-the-loop interruption.

    No state updates are performed here; the graph interrupts before this node.
    """
    return {"messages": []}