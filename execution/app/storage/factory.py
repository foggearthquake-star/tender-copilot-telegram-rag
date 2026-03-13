from __future__ import annotations

from app.core.config import settings
from app.storage.postgres_repository import PostgresRepository
from app.storage.repository import JsonRepository


def build_repository():
    if settings.database_url:
        try:
            return PostgresRepository(settings.database_url)
        except Exception:
            pass
    return JsonRepository(settings.storage_path)
