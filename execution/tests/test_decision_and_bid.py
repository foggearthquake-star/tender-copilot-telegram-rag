from app.schemas.models import CompanyProfile, TenderFacts
from app.services.bid_writer import BidWriter
from app.services.decision_engine import DecisionEngine
from app.services.vector_service import VectorRecord


def test_decision_no_go_on_limit() -> None:
    profile = CompanyProfile(
        company_name="ООО Тест",
        categories=["it"],
        regions=["Россия"],
        max_contract_value_rub=1_000_000,
        min_margin_percent=10,
        required_certificates=[],
        stop_factors=[],
    )
    facts = TenderFacts(contract_value_rub=5_000_000, deadline="2026-05-01")
    ev = [VectorRecord("1", "doc.pdf", "chunk_1", "Цена контракта", [0.0])]
    report = DecisionEngine().decide(profile, facts, ev)
    assert report.status.value == "NO_GO"


def test_bid_writer_has_required_sections() -> None:
    profile = CompanyProfile(company_name="ООО Тест")
    facts = TenderFacts(deadline="2026-05-01", contract_value_rub=100000)
    report = DecisionEngine().decide(profile, facts, [])
    outline = BidWriter().build_outline(profile, facts, report)
    assert len(outline.required_sections) >= 3
