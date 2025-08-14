from pydantic import BaseModel
from typing import List, Dict, Any
from uuid import UUID

class RunRequest(BaseModel):
    rounds: int = 2
    victim_ids: List[int]
    method_ids: List[int]
    max_turns: int | None = None

class RunSummary(BaseModel):
    run_id: UUID
    pre_rate: float
    post_rate: float
    delta_pp: float
    by_age_method: Dict[str, Any] = {}
