from __future__ import annotations

from cons_trukt.retrieval.evaluation import (
    RetrievalQuery,
    evaluate_retrieval,
)
from cons_trukt.retrieval.tfidf_store import TfidfPrecedentStore
from cons_trukt.schemas import KnowledgeDocument


def _documents() -> list[KnowledgeDocument]:
    return [
        KnowledgeDocument(
            "slope",
            "Steep hillside permits require geotechnical slope stability review.",
            {"source": "slope-guidance", "type": "permit_guidance"},
        ),
        KnowledgeDocument(
            "wetland",
            "Wetland buffers require environmental review before grading.",
            {"source": "wetland-guidance", "type": "permit_guidance"},
        ),
    ]


def test_tfidf_store_ranks_relevant_precedent_first():
    store = TfidfPrecedentStore(_documents())

    hits = store.query("geotechnical review for steep slope", n_results=2)

    assert hits[0].source == "slope-guidance"
    assert hits[0].score > hits[1].score


def test_tfidf_store_expands_construction_domain_aliases():
    store = TfidfPrecedentStore(_documents())

    hit = store.query(
        "geotechnical review for steep hillside construction",
        n_results=1,
    )[0]

    assert hit.source == "slope-guidance"


def test_tfidf_store_round_trip(tmp_path):
    path = TfidfPrecedentStore(_documents()).save(tmp_path / "index.json")

    restored = TfidfPrecedentStore.load(path)

    assert restored.query("wetland environmental buffer", 1)[0].source == ("wetland-guidance")


def test_retrieval_metrics_are_reproducible():
    store = TfidfPrecedentStore(_documents())
    queries = [
        RetrievalQuery(
            query_id="q1",
            query="steep slope stability",
            expected_sources=("slope-guidance",),
        ),
        RetrievalQuery(
            query_id="q2",
            query="wetland buffer review",
            expected_sources=("wetland-guidance",),
        ),
    ]

    metrics = evaluate_retrieval(store, queries)

    assert metrics.recall_at_1 == 1.0
    assert metrics.recall_at_3 == 1.0
    assert metrics.mean_reciprocal_rank == 1.0


def test_safe_retrieval_rejects_out_of_domain_query():
    decision = TfidfPrecedentStore(_documents()).query_safe("recommend a science fiction movie")

    assert decision.accepted is False
    assert decision.hits == ()


def test_safe_retrieval_accepts_supported_query():
    decision = TfidfPrecedentStore(_documents()).query_safe(
        "geotechnical review for steep hillside"
    )

    assert decision.accepted is True
    assert decision.hits[0].source == "slope-guidance"
