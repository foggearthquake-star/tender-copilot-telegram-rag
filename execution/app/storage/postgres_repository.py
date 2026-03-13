from __future__ import annotations

import json
from typing import Any

from psycopg import connect
from psycopg.rows import dict_row

from app.schemas.models import CompanyProfile, TenderRun


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._init_db()

    def _conn(self):
        return connect(self.database_url, row_factory=dict_row)

    def _init_db(self) -> None:
        ddl = """
        CREATE TABLE IF NOT EXISTS profiles (
            user_id BIGINT PRIMARY KEY,
            data JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS tenders (
            user_id BIGINT NOT NULL,
            tender_id TEXT NOT NULL,
            data JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, tender_id)
        );
        CREATE INDEX IF NOT EXISTS idx_tenders_user_created_at ON tenders(user_id, created_at DESC);
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
            conn.commit()

    def save_profile(self, user_id: int, profile: CompanyProfile) -> None:
        payload = json.dumps(profile.model_dump(mode="json"), ensure_ascii=False)
        sql = """
        INSERT INTO profiles(user_id, data, updated_at)
        VALUES (%s, %s::jsonb, NOW())
        ON CONFLICT (user_id)
        DO UPDATE SET data = EXCLUDED.data, updated_at = NOW();
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, payload))
            conn.commit()

    def get_profile(self, user_id: int) -> CompanyProfile | None:
        sql = "SELECT data FROM profiles WHERE user_id = %s"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
        if not row:
            return None
        return CompanyProfile(**row["data"])

    def save_tender_run(self, user_id: int, run: TenderRun) -> None:
        payload = json.dumps(run.model_dump(mode="json"), ensure_ascii=False)
        sql = """
        INSERT INTO tenders(user_id, tender_id, data, created_at)
        VALUES (%s, %s, %s::jsonb, NOW())
        ON CONFLICT (user_id, tender_id)
        DO UPDATE SET data = EXCLUDED.data;
        """
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, run.tender_input.tender_id, payload))
            conn.commit()

    def get_tender_run(self, user_id: int, tender_id: str) -> TenderRun | None:
        sql = "SELECT data FROM tenders WHERE user_id = %s AND tender_id = %s"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, tender_id))
                row = cur.fetchone()
        if not row:
            return None
        return TenderRun(**row["data"])

    def get_last_tender_run(self, user_id: int) -> TenderRun | None:
        sql = "SELECT data FROM tenders WHERE user_id = %s ORDER BY created_at DESC LIMIT 1"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id,))
                row = cur.fetchone()
        if not row:
            return None
        return TenderRun(**row["data"])

    def get_recent_tender_runs(self, user_id: int, limit: int = 5) -> list[TenderRun]:
        sql = "SELECT data FROM tenders WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, limit))
                rows = cur.fetchall()
        return [TenderRun(**row["data"]) for row in rows]
