from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.schemas.models import TenderRun


def append_run_audit(run: TenderRun) -> None:
    path = Path(settings.audit_log_path)
    entry = {
        "run_id": run.run_id,
        "tender_id": run.tender_input.tender_id,
        "status": run.status,
        "total_duration_ms": run.total_duration_ms,
        "warnings": run.warnings,
        "stages": [
            {
                "stage": s.stage,
                "status": s.status,
                "duration_ms": s.duration_ms,
                "error": s.error,
                "meta": s.meta,
            }
            for s in run.stages
        ],
        "run_started_at": run.run_started_at.isoformat() if run.run_started_at else None,
        "run_finished_at": run.run_finished_at.isoformat() if run.run_finished_at else None,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
