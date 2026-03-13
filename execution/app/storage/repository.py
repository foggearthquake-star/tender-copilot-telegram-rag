from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.models import CompanyProfile, TenderRun


class JsonRepository:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if not self.path.exists():
            self._write({"profiles": {}, "tenders": {}})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def save_profile(self, user_id: int, profile: CompanyProfile) -> None:
        data = self._read()
        data["profiles"][str(user_id)] = profile.model_dump()
        self._write(data)

    def get_profile(self, user_id: int) -> CompanyProfile | None:
        data = self._read()
        raw = data["profiles"].get(str(user_id))
        return CompanyProfile(**raw) if raw else None

    def save_tender_run(self, user_id: int, run: TenderRun) -> None:
        data = self._read()
        user_tenders = data["tenders"].setdefault(str(user_id), {})
        user_tenders[run.tender_input.tender_id] = run.model_dump(mode="json")
        self._write(data)

    def get_tender_run(self, user_id: int, tender_id: str) -> TenderRun | None:
        data = self._read()
        raw = data["tenders"].get(str(user_id), {}).get(tender_id)
        return TenderRun(**raw) if raw else None

    def get_last_tender_run(self, user_id: int) -> TenderRun | None:
        data = self._read()
        user_tenders = data["tenders"].get(str(user_id), {})
        if not user_tenders:
            return None
        tender_id = sorted(user_tenders.keys())[-1]
        return TenderRun(**user_tenders[tender_id])

    def get_recent_tender_runs(self, user_id: int, limit: int = 5) -> list[TenderRun]:
        data = self._read()
        user_tenders = data["tenders"].get(str(user_id), {})
        if not user_tenders:
            return []
        keys = sorted(user_tenders.keys(), reverse=True)[:limit]
        return [TenderRun(**user_tenders[key]) for key in keys]
