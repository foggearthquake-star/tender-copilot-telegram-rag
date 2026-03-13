from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class VectorRecord:
    chunk_id: str
    doc_name: str
    fragment_ref: str
    text: str
    vector: list[float]


def _hash_embed(text: str, dim: int = 96) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(dim):
        b = digest[i % len(digest)]
        values.append((b / 255.0) * 2 - 1)
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class LocalVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, list[VectorRecord]] = {}

    def upsert(self, namespace: str, records: list[VectorRecord]) -> None:
        self.records[namespace] = records

    def search(self, namespace: str, query: str, top_k: int = 5) -> list[VectorRecord]:
        entries = self.records.get(namespace, [])
        qv = _hash_embed(query)
        scored = sorted(entries, key=lambda r: _cosine(r.vector, qv), reverse=True)
        return scored[:top_k]


class VectorService:
    def __init__(self) -> None:
        self.backend = settings.vector_backend.lower()
        self.local = LocalVectorStore()
        self.qdrant_client = None
        self.pinecone_index = None

        if self.backend == "qdrant":
            self._try_init_qdrant()
        elif self.backend == "pinecone":
            self._try_init_pinecone()

    def _try_init_qdrant(self) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
        except Exception:
            self.backend = "local"
            return

        if not settings.qdrant_url:
            self.backend = "local"
            return

        try:
            self.qdrant_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
            collections = [c.name for c in self.qdrant_client.get_collections().collections]
            if settings.qdrant_collection not in collections:
                self.qdrant_client.create_collection(
                    collection_name=settings.qdrant_collection,
                    vectors_config=VectorParams(size=96, distance=Distance.COSINE),
                )
        except Exception:
            self.qdrant_client = None
            self.backend = "local"

    def _try_init_pinecone(self) -> None:
        try:
            from pinecone import Pinecone
        except Exception:
            self.backend = "local"
            return

        if not settings.pinecone_api_key:
            self.backend = "local"
            return

        try:
            pc = Pinecone(api_key=settings.pinecone_api_key)
            self.pinecone_index = pc.Index(settings.pinecone_index)
        except Exception:
            self.pinecone_index = None
            self.backend = "local"

    def _to_records(self, namespace: str, doc_name: str, chunks: list[str]) -> list[VectorRecord]:
        return [
            VectorRecord(
                chunk_id=f"{namespace}:{idx}",
                doc_name=doc_name,
                fragment_ref=f"chunk_{idx + 1}",
                text=chunk,
                vector=_hash_embed(chunk),
            )
            for idx, chunk in enumerate(chunks)
        ]

    def index_chunks(self, namespace: str, doc_name: str, chunks: list[str]) -> None:
        records = self._to_records(namespace, doc_name, chunks)

        if self.backend == "qdrant" and self.qdrant_client:
            try:
                self.qdrant_client.upsert(
                    collection_name=settings.qdrant_collection,
                    points=[
                        {
                            "id": rec.chunk_id,
                            "vector": rec.vector,
                            "payload": {
                                "namespace": namespace,
                                "doc_name": rec.doc_name,
                                "fragment_ref": rec.fragment_ref,
                                "text": rec.text,
                            },
                        }
                        for rec in records
                    ],
                )
                return
            except Exception:
                self.backend = "local"

        if self.backend == "pinecone" and self.pinecone_index:
            try:
                self.pinecone_index.upsert(
                    vectors=[
                        {
                            "id": rec.chunk_id,
                            "values": rec.vector,
                            "metadata": {
                                "namespace": namespace,
                                "doc_name": rec.doc_name,
                                "fragment_ref": rec.fragment_ref,
                                "text": rec.text,
                            },
                        }
                        for rec in records
                    ],
                    namespace=namespace,
                )
                return
            except Exception:
                self.backend = "local"

        existing = self.local.records.get(namespace, [])
        self.local.upsert(namespace, existing + records)

    def retrieve(self, namespace: str, query: str, top_k: int = 5) -> list[VectorRecord]:
        qv = _hash_embed(query)

        if self.backend == "qdrant" and self.qdrant_client:
            try:
                hits = self.qdrant_client.query_points(
                    collection_name=settings.qdrant_collection,
                    query=qv,
                    limit=top_k,
                    query_filter={"must": [{"key": "namespace", "match": {"value": namespace}}]},
                ).points
                return [
                    VectorRecord(
                        chunk_id=str(hit.id),
                        doc_name=str(hit.payload.get("doc_name", "unknown")),
                        fragment_ref=str(hit.payload.get("fragment_ref", "chunk")),
                        text=str(hit.payload.get("text", "")),
                        vector=qv,
                    )
                    for hit in hits
                ]
            except Exception:
                self.backend = "local"

        if self.backend == "pinecone" and self.pinecone_index:
            try:
                result = self.pinecone_index.query(namespace=namespace, vector=qv, top_k=top_k, include_metadata=True)
                matches = result.get("matches", [])
                return [
                    VectorRecord(
                        chunk_id=str(match.get("id", "")),
                        doc_name=str(match.get("metadata", {}).get("doc_name", "unknown")),
                        fragment_ref=str(match.get("metadata", {}).get("fragment_ref", "chunk")),
                        text=str(match.get("metadata", {}).get("text", "")),
                        vector=qv,
                    )
                    for match in matches
                ]
            except Exception:
                self.backend = "local"

        return self.local.search(namespace, query, top_k=top_k)
