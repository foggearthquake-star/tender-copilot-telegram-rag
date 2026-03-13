from pathlib import Path

from app.schemas.models import CompanyProfile, TenderInput, TenderRun
from app.storage.repository import JsonRepository


def test_repository_recent_runs_limit(tmp_path: Path) -> None:
    repo_path = tmp_path / "storage.json"
    repo = JsonRepository(str(repo_path))
    user_id = 1

    profile = CompanyProfile(company_name="ООО Тест")
    repo.save_profile(user_id, profile)

    for i in range(7):
        tender_input = TenderInput(tender_id=f"t{i}", uploaded_files=[])
        run = TenderRun(run_id=f"r{i}", tender_input=tender_input, status="report_ready")
        repo.save_tender_run(user_id, run)

    recent = repo.get_recent_tender_runs(user_id, limit=5)
    assert len(recent) == 5
    assert recent[0].tender_input.tender_id == "t6"
