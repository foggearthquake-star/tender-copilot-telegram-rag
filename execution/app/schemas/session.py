from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionState:
    mode: str = "idle"
    pending_files: list[str] = field(default_factory=list)
    profile_step_index: int = 0
    draft_profile: dict[str, object] = field(default_factory=dict)
    tender_meta_deadline: str | None = None
    tender_meta_price_hint: float | None = None
    tender_meta_comment: str | None = None
