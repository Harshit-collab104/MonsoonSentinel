from datetime import datetime, timezone
from typing import Any, List, Dict
from pydantic import BaseModel, Field
from app.core.enums import Severity

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RiskFactorBreakdown(BaseModel):
    factor_name: str
    raw_value: Any
    normalized_score: float = Field(..., ge=0.0, le=100.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    contribution: float = Field(..., ge=0.0, le=100.0)
    is_missing: bool = False
    notes: str = ""

class RiskAssessment(BaseModel):
    incident_id: str
    calculated_at: datetime = Field(default_factory=utc_now)
    risk_score: float = Field(..., ge=0.0, le=100.0)
    severity: Severity
    factors: List[RiskFactorBreakdown] = []
    missing_factors: List[str] = []
    uncertainty_penalty: float = 0.0
    formula_used: str = "min(100, sum(weight_i * normalized_score_i) + uncertainty_penalty)"
    explanation: str
    is_synthetic_data: bool = True

class PriorityScore(BaseModel):
    incident_id: str
    priority_rank: int = 1
    urgency_score: float = 0.0
    evaluated_at: datetime = Field(default_factory=utc_now)
    ranking_factors: Dict[str, Any] = {}
    recommendation_summary: str = ""
