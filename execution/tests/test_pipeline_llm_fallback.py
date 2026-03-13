from pathlib import Path

from docx import Document

from app.schemas.models import CompanyProfile
from app.services.pipeline import TenderPipeline


class BrokenLLM:
    def refine_decision(self, decision_payload, context_payload):
        raise RuntimeError("llm down")

    def enrich_bid_outline(self, outline_payload, context_payload):
        raise RuntimeError("llm down")


def test_pipeline_survives_llm_failures(tmp_path: Path) -> None:
    docx_path = tmp_path / "tender.docx"
    doc = Document()
    doc.add_paragraph("Цена контракта 500 000 руб. Дедлайн 2026-08-01. Требуется лицензия.")
    doc.save(docx_path)

    profile = CompanyProfile(
        company_name="ООО Тест",
        max_contract_value_rub=2_000_000,
        required_certificates=["лицензия"],
    )
    pipeline = TenderPipeline()
    pipeline.llm_service = BrokenLLM()

    run = pipeline.run(profile, [str(docx_path)], None, None, None)

    assert run.status == "report_ready"
    assert run.decision is not None
    assert len(run.warnings) >= 1
    assert any("llm_" in w for w in run.warnings)
