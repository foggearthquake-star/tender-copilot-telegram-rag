from pathlib import Path

from app.schemas.models import CompanyProfile
from app.services.pipeline import TenderPipeline


def test_pipeline_failsafe_on_bad_extension(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("nope", encoding="utf-8")

    profile = CompanyProfile(company_name="ООО Тест", max_contract_value_rub=1000000)
    run = TenderPipeline().run(
        profile=profile,
        files=[str(bad_file)],
        deadline=None,
        price_hint_rub=None,
        comment=None,
    )

    assert run.status == "failed"
    assert run.decision is not None
    assert run.decision.status.value == "REVIEW"
    assert run.total_duration_ms is not None
    assert any(stage.status == "failed" for stage in run.stages)
