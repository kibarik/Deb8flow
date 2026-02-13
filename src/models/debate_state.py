from typing import NotRequired, List, Dict, Literal
from .debate_stage import DebateStage

class DebateState(TypedDict):
    debate_topic: str
    positions: Dict[str, str]
    messages: List[DebateMessage]
    stage: NotRequired[str]
    speaker: NotRequired[str]
    opening_statement_pro_agent: NotRequired[str]
    times_pro_fact_checked: NotRequired[int]
    times_con_fact_checked: NotRequired[int]
    document_input: NotRequired[str]
