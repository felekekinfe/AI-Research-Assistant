from typing import Annotated, TypedDict, List, Optional
import operator

class AgentState(TypedDict):
    task: str
    research_data: Annotated[str, operator.add] 
    draft: Optional[str]
    is_valid: bool
    feedback: Optional[str]
    revision_count: int
    refined_query: Optional[str]
    messages: Annotated[list, operator.add] 