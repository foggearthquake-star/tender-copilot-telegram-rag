from datetime import UTC, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DecisionStatus(str, Enum):
    GO = "GO"
    REVIEW = "REVIEW"
    NO_GO = "NO_GO"


class EvidenceItem(BaseModel):
    doc_name: str
    fragment_ref: str
    quote: str
    relevance: float = Field(ge=0.0, le=1.0)


class CompanyProfile(BaseModel):
    company_name: str
    categories: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    max_contract_value_rub: float = 0.0
    min_margin_percent: float = 0.0
    required_certificates: list[str] = Field(default_factory=list)
    stop_factors: list[str] = Field(default_factory=list)
    company_summary: str = ""
    focus_areas: list[str] = Field(default_factory=list)
    project_examples: list[str] = Field(default_factory=list)
    knowledge_text: str = ""


class TenderInput(BaseModel):
    tender_id: str
    uploaded_files: list[str]
    deadline: Optional[str] = None
    price_hint_rub: Optional[float] = None
    comment: Optional[str] = None


class TenderFacts(BaseModel):
    customer_name: Optional[str] = None
    tender_subject: Optional[str] = None
    contract_value_rub: Optional[float] = None
    deadline: Optional[str] = None
    required_certificates: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    payment_terms: Optional[str] = None
    obligations: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)
    special_terms: list[str] = Field(default_factory=list)


class DecisionReport(BaseModel):
    status: DecisionStatus
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reason: str
    overall_score: int = Field(default=0, ge=0, le=100)
    fit_score: int = Field(default=0, ge=0, le=100)
    evidence_score: int = Field(default=0, ge=0, le=100)
    completeness_score: int = Field(default=0, ge=0, le=100)
    risk_score: int = Field(default=0, ge=0, le=100)
    reasons: list[str]
    risks: list[str]
    evidence: list[EvidenceItem]
    next_actions: list[str]
    latency_ms: int
    cost_estimate_rub: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BidDraftOutline(BaseModel):
    title: str
    required_sections: list[str]
    recommended_sections: list[str]
    missing_information: list[str]
    submission_checklist: list[str]


class StageLog(BaseModel):
    stage: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "running"
    error: Optional[str] = None
    meta: dict[str, str] = Field(default_factory=dict)


class TenderRun(BaseModel):
    run_id: str = ""
    tender_input: TenderInput
    facts: Optional[TenderFacts] = None
    decision: Optional[DecisionReport] = None
    bid_outline: Optional[BidDraftOutline] = None
    report_path: Optional[str] = None
    status: str = "upload_received"
    run_started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_finished_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    stages: list[StageLog] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

