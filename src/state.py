from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    task: str
    research_data: Optional[str]
    draft: Optional[str]
    feedback: Optional[str]
    revision_count: int
    messages: List[str]  # Used for UI logs