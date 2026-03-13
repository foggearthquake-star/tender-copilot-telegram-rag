# Data Contracts (v1)

## CompanyProfile
- company_name: str
- categories: list[str]
- regions: list[str]
- max_contract_value_rub: float
- min_margin_percent: float
- required_certificates: list[str]
- stop_factors: list[str]

## TenderInput
- tender_id: str
- uploaded_files: list[str]
- deadline: str | null
- price_hint_rub: float | null
- comment: str | null

## TenderFacts
- customer_name: str | null
- contract_value_rub: float | null
- deadline: str | null
- required_certificates: list[str]
- regions: list[str]
- payment_terms: str | null
- obligations: list[str]

## DecisionReport
- status: GO | REVIEW | NO_GO
- confidence: float
- confidence_reason: str
- reasons: list[str]
- risks: list[str]
- evidence: list[EvidenceItem]
- next_actions: list[str]
- latency_ms: int
- cost_estimate_rub: float

## BidDraftOutline
- title: str
- required_sections: list[str]
- recommended_sections: list[str]
- missing_information: list[str]
- submission_checklist: list[str]

## EvidenceItem
- doc_name: str
- fragment_ref: str
- quote: str
- relevance: float

## TenderRun (operational)
- run_id: str
- status: str
- run_started_at: datetime
- run_finished_at: datetime | null
- total_duration_ms: int | null
- stages: list[StageLog]

## StageLog
- stage: str
- started_at: datetime
- ended_at: datetime | null
- duration_ms: int | null
- status: running | completed | failed
- error: str | null
- meta: dict[str, str]
