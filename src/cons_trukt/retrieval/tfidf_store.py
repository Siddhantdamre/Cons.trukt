"""Dependency-free fitted TF-IDF precedent retrieval."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cons_trukt.schemas import KnowledgeDocument, Precedent

STOPWORDS = frozenset(
    {
        "a",
        "all",
        "an",
        "and",
        "are",
        "before",
        "for",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)

DOMAIN_ALIASES = {
    "geotech": "geotechnical",
    "hill": "slope",
    "hillside": "slope",
    "steep": "slope",
    "sound": "noise",
    "wheelchair": "accessible",
}


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw_token in re.findall(r"[a-z0-9]+", text.lower()):
        if len(raw_token) <= 1 or raw_token in STOPWORDS:
            continue
        token = DOMAIN_ALIASES.get(raw_token, raw_token)
        if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        tokens.append(token)
    return tokens


@dataclass(frozen=True)
class RetrievalDecision:
    accepted: bool
    reason: str
    top_score: float
    score_margin: float
    query_coverage: float
    hits: tuple[Precedent, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TfidfPrecedentStore:
    """A serializable local precedent index with cosine-similarity ranking."""

    def __init__(self, documents: Iterable[KnowledgeDocument] = ()) -> None:
        self.documents: list[KnowledgeDocument] = []
        self.idf: dict[str, float] = {}
        self.document_vectors: list[dict[str, float]] = []
        if documents:
            self.upsert_documents(documents)

    def upsert_documents(self, documents: Iterable[KnowledgeDocument]) -> int:
        incoming = list(documents)
        if not incoming:
            return 0
        by_id = {document.doc_id: document for document in self.documents}
        by_id.update({document.doc_id: document for document in incoming})
        self.documents = [by_id[doc_id] for doc_id in sorted(by_id)]
        self._fit()
        return len(incoming)

    def query(self, question: str, n_results: int | None = None) -> list[Precedent]:
        if not self.documents:
            return []
        limit = len(self.documents) if n_results is None else max(0, n_results)
        if limit == 0:
            return []

        counts = Counter(tokenize(question))
        total = max(1, sum(counts.values()))
        query_vector = _normalize(
            {
                term: (count / total) * self.idf[term]
                for term, count in counts.items()
                if term in self.idf
            }
        )
        ranked = sorted(
            zip(self.documents, self.document_vectors, strict=True),
            key=lambda pair: (
                -_dot(query_vector, pair[1]),
                pair[0].doc_id,
            ),
        )
        return [
            Precedent(
                content=document.content,
                source=str(document.metadata.get("source", "offline-index")),
                kind=str(document.metadata.get("type", "historical_permits")),
                score=round(_dot(query_vector, vector), 6),
            )
            for document, vector in ranked[:limit]
        ]

    def query_safe(
        self,
        question: str,
        n_results: int = 3,
        minimum_score: float = 0.14,
        minimum_query_coverage: float = 0.35,
    ) -> RetrievalDecision:
        """Retrieve precedents and reject unsupported or out-of-domain queries."""
        hits = tuple(self.query(question, n_results=max(2, n_results)))
        query_terms = set(tokenize(question))
        known_terms = query_terms & self.idf.keys()
        query_coverage = len(known_terms) / len(query_terms) if query_terms else 0.0
        top_score = hits[0].score or 0.0 if hits else 0.0
        second_score = hits[1].score or 0.0 if len(hits) > 1 else 0.0
        score_margin = top_score - second_score

        if not question.strip():
            reason = "No query text was provided."
        elif top_score < minimum_score:
            reason = "No precedent reached the minimum relevance threshold."
        elif query_coverage < minimum_query_coverage:
            reason = "Too little of the query is represented in the fitted corpus."
        else:
            return RetrievalDecision(
                accepted=True,
                reason="Retrieved evidence passed relevance and query-coverage thresholds.",
                top_score=round(top_score, 6),
                score_margin=round(score_margin, 6),
                query_coverage=round(query_coverage, 6),
                hits=hits[:n_results],
            )

        return RetrievalDecision(
            accepted=False,
            reason=reason,
            top_score=round(top_score, 6),
            score_margin=round(score_margin, 6),
            query_coverage=round(query_coverage, 6),
            hits=(),
        )

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": "tfidf_precedent_store",
            "version": 1,
            "documents": [
                {
                    "doc_id": document.doc_id,
                    "content": document.content,
                    "metadata": document.metadata,
                }
                for document in self.documents
            ],
            "idf": self.idf,
            "document_vectors": self.document_vectors,
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> TfidfPrecedentStore:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("model_type") != "tfidf_precedent_store":
            raise ValueError("unsupported precedent index artifact")

        store = cls()
        store.documents = [
            KnowledgeDocument(
                doc_id=str(document["doc_id"]),
                content=str(document["content"]),
                metadata=dict(document["metadata"]),
            )
            for document in payload["documents"]
        ]
        store.idf = {str(term): float(value) for term, value in payload["idf"].items()}
        store.document_vectors = [
            {str(term): float(value) for term, value in vector.items()}
            for vector in payload["document_vectors"]
        ]
        return store

    def _fit(self) -> None:
        token_counts = [Counter(tokenize(document.content)) for document in self.documents]
        document_frequency: Counter[str] = Counter()
        for counts in token_counts:
            document_frequency.update(counts.keys())

        document_count = len(self.documents)
        self.idf = {
            term: math.log((1 + document_count) / (1 + frequency)) + 1.0
            for term, frequency in document_frequency.items()
        }
        self.document_vectors = [
            _normalize(
                {
                    term: (count / max(1, sum(counts.values()))) * self.idf[term]
                    for term, count in counts.items()
                }
            )
            for counts in token_counts
        ]


def load_corpus(path: str | Path) -> list[KnowledgeDocument]:
    documents = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        documents.append(
            KnowledgeDocument(
                doc_id=str(payload["doc_id"]),
                content=str(payload["content"]),
                metadata=dict(payload.get("metadata", {})),
            )
        )
    if not documents:
        raise ValueError("precedent corpus is empty")
    return documents


def _normalize(vector: dict[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm == 0:
        return vector
    return {term: value / norm for term, value in vector.items()}


def _dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())
