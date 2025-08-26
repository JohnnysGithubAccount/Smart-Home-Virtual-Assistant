from typing import TypedDict, Optional

class AgentState(TypedDict):
    user_input: str
    confirmed: bool
    action_result: Optional[str]
    memory: dict
