from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    email_data: Dict[str, Any]
    errors: Annotated[List[str], operator.add]
    next_step: str