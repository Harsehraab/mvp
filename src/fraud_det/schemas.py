from typing import List, Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    id: str
    amount: float
    currency: str
    timestamp: str
    metadata: Optional[dict] = None


class InvestigateArgs(BaseModel):
    transactions_batch: List[Transaction]


class Indicator(BaseModel):
    name: str
    value: str


class InvestigateItem(BaseModel):
    id: str
    risk_score: float
    indicators: List[Indicator]
    related_entities: List[str]
    rationale: str


class InvestigateOutput(BaseModel):
    results: List[InvestigateItem]


class TriageArgs(BaseModel):
    cases: List[InvestigateItem]


class TriageItem(BaseModel):
    case_id: str
    severity: str
    recommended_actions: List[str]
    confidence: float


class TriageOutput(BaseModel):
    cases: List[TriageItem]


class ReportArgs(BaseModel):
    cases: List[TriageItem]


class ReportOutput(BaseModel):
    report_markdown: str
