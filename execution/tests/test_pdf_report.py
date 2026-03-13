from pathlib import Path

from app.reporting.pdf_report import PdfReportService
from app.schemas.models import BidDraftOutline, CompanyProfile, DecisionReport, DecisionStatus, EvidenceItem, TenderFacts


def test_pdf_report_created(tmp_path: Path) -> None:
    profile = CompanyProfile(company_name="ООО Тест")
    facts = TenderFacts(contract_value_rub=1000, deadline="2026-06-01")
    decision = DecisionReport(
        status=DecisionStatus.REVIEW,
        confidence=0.6,
        confidence_reason="Недостаточно данных",
        reasons=["Причина"],
        risks=["Риск"],
        evidence=[EvidenceItem(doc_name="doc.pdf", fragment_ref="chunk_1", quote="quote", relevance=0.7)],
        next_actions=["Шаг"],
        latency_ms=10,
        cost_estimate_rub=0.2,
    )
    outline = BidDraftOutline(
        title="Черновик",
        required_sections=["A"],
        recommended_sections=["B"],
        missing_information=["C"],
        submission_checklist=["D"],
    )

    path = tmp_path / "out.pdf"
    out = PdfReportService().build_report(path, profile, facts, decision, outline)
    assert Path(out).exists()
