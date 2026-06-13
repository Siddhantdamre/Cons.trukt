"""Vector store interfaces and Chroma implementation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from cons_trukt.config import RetrievalSettings
from cons_trukt.exceptions import RetrievalError
from cons_trukt.schemas import KnowledgeDocument, Precedent


class PrecedentStore(Protocol):
    def query(self, question: str, n_results: int | None = None) -> list[Precedent]:
        """Return relevant historical precedents."""

    def upsert_documents(self, documents: Iterable[KnowledgeDocument]) -> int:
        """Upsert documents and return the number written."""


@dataclass
class InMemoryPrecedentStore:
    """Small test double that follows the same interface as the Chroma adapter."""

    documents: list[KnowledgeDocument]

    def query(self, question: str, n_results: int | None = None) -> list[Precedent]:
        limit = n_results or len(self.documents)
        return [
            Precedent(content=doc.content, source=str(doc.metadata.get("source", "memory")))
            for doc in self.documents[:limit]
        ]

    def upsert_documents(self, documents: Iterable[KnowledgeDocument]) -> int:
        docs = list(documents)
        self.documents.extend(docs)
        return len(docs)


class ChromaPrecedentStore:
    """ChromaDB-backed precedent memory."""

    def __init__(self, settings: RetrievalSettings) -> None:
        self.settings = settings
        try:
            import chromadb
        except ImportError as exc:
            raise RetrievalError("chromadb is required for Chroma precedent retrieval.") from exc

        try:
            client = chromadb.PersistentClient(path=str(settings.chroma_path))
            self.collection = client.get_or_create_collection(name=settings.collection_name)
        except Exception as exc:
            raise RetrievalError(
                f"Could not initialize Chroma at {settings.chroma_path}: {exc}"
            ) from exc

    def query(self, question: str, n_results: int | None = None) -> list[Precedent]:
        limit = n_results or self.settings.n_results
        try:
            results = self.collection.query(query_texts=[question], n_results=limit)
        except Exception as exc:
            raise RetrievalError(f"Chroma query failed: {exc}") from exc

        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        precedents: list[Precedent] = []
        for index, content in enumerate(documents):
            metadata = metadatas[index] if index < len(metadatas) else {}
            score = distances[index] if index < len(distances) else None
            precedents.append(
                Precedent(
                    content=str(content),
                    source=str(metadata.get("source", "unknown")),
                    kind=str(metadata.get("type", "historical_permits")),
                    score=float(score) if score is not None else None,
                )
            )
        return precedents

    def upsert_documents(self, documents: Iterable[KnowledgeDocument]) -> int:
        docs = list(documents)
        if not docs:
            return 0

        written = 0
        for start in range(0, len(docs), self.settings.batch_size):
            batch = docs[start : start + self.settings.batch_size]
            try:
                self.collection.upsert(
                    documents=[doc.content for doc in batch],
                    metadatas=[doc.metadata for doc in batch],
                    ids=[doc.doc_id for doc in batch],
                )
            except Exception as exc:
                raise RetrievalError(f"Chroma upsert failed: {exc}") from exc
            written += len(batch)
        return written
