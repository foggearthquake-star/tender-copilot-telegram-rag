from __future__ import annotations

import json
from dataclasses import asdict

from redis import Redis

from app.schemas.session import SessionState


class SessionStore:
    def __init__(self, redis_url: str = "") -> None:
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = Redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
        self.memory: dict[int, SessionState] = {}

    def _key(self, user_id: int) -> str:
        return f"tender:session:{user_id}"

    def get(self, user_id: int) -> SessionState:
        if user_id in self.memory:
            return self.memory[user_id]
        if self.redis_client:
            try:
                raw = self.redis_client.get(self._key(user_id))
                if raw:
                    data = json.loads(raw)
                    session = SessionState(**data)
                    self.memory[user_id] = session
                    return session
            except Exception:
                self.redis_client = None
        session = SessionState()
        self.memory[user_id] = session
        return session

    def save(self, user_id: int, session: SessionState) -> None:
        self.memory[user_id] = session
        if self.redis_client:
            try:
                self.redis_client.set(self._key(user_id), json.dumps(asdict(session), ensure_ascii=False))
            except Exception:
                self.redis_client = None

    def clear(self, user_id: int) -> None:
        self.memory[user_id] = SessionState()
        if self.redis_client:
            try:
                self.redis_client.delete(self._key(user_id))
            except Exception:
                self.redis_client = None
