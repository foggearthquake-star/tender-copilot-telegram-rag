import json
from pathlib import Path

from app.core.audit import append_run_audit
from app.schemas.models import TenderInput, TenderRun


def test_append_run_audit_writes_jsonl(tmp_path: Path, monkeypatch) -> None:
    from app.core import config as cfg

    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(cfg.settings, "audit_log_path", str(audit_path))

    run = TenderRun(run_id="r1", tender_input=TenderInput(tender_id="t1", uploaded_files=[]), status="report_ready")
    append_run_audit(run)

    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["run_id"] == "r1"
    assert payload["status"] == "report_ready"
