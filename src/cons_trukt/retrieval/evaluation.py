"""Evaluation utilities for precedent retrieval."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from cons_trukt.retrieval.tfidf_store import TfidfPrecedentStore
from cons_trukt.statistics import Interval, wilson_interval


@dataclass(frozen=True)
class RetrievalQuery:
    query_id: str
    query: str
    expected_sources: tuple[str, ...]
    should_abstain: bool = False


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_1: float
    recall_at_3: float
    mean_reciprocal_rank: float
    accepted_query_accuracy: float
    out_of_domain_rejection_rate: float
    false_acceptance_rate: float
    queries: int
    recall_at_1_ci95: Interval = (0.0, 0.0)
    recall_at_3_ci95: Interval = (0.0, 0.0)
    out_of_domain_rejection_ci95: Interval = (0.0, 0.0)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = asdict(self)
        payload["recall_at_1_ci95"] = list(self.recall_at_1_ci95)
        payload["recall_at_3_ci95"] = list(self.recall_at_3_ci95)
        payload["out_of_domain_rejection_ci95"] = list(self.out_of_domain_rejection_ci95)
        return payload


def load_queries(path: str | Path) -> list[RetrievalQuery]:
    queries = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        queries.append(
            RetrievalQuery(
                query_id=str(payload["id"]),
                query=str(payload["query"]),
                expected_sources=tuple(payload["expected_sources"]),
                should_abstain=bool(payload.get("should_abstain", False)),
            )
        )
    if not queries:
        raise ValueError("retrieval query set is empty")
    return queries


def evaluate_retrieval(
    store: TfidfPrecedentStore,
    queries: list[RetrievalQuery],
) -> RetrievalMetrics:
    if not queries:
        raise ValueError("at least one retrieval query is required")

    relevant_queries = [query for query in queries if not query.should_abstain]
    ood_queries = [query for query in queries if query.should_abstain]
    hits_at_1 = 0
    hits_at_3 = 0
    reciprocal_ranks = []
    accepted_correct = 0
    accepted_total = 0
    ood_rejected = 0
    for query in queries:
        decision = store.query_safe(query.query, n_results=3)
        if query.should_abstain:
            ood_rejected += int(not decision.accepted)
            continue

        precedents = store.query(query.query, n_results=3)
        sources = [precedent.source for precedent in precedents]
        expected = set(query.expected_sources)
        hits_at_1 += int(bool(expected & set(sources[:1])))
        hits_at_3 += int(bool(expected & set(sources[:3])))
        rank = next(
            (index for index, source in enumerate(sources, start=1) if source in expected),
            None,
        )
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
        if decision.accepted:
            accepted_total += 1
            accepted_correct += int(bool(expected & {decision.hits[0].source}))

    relevant_count = len(relevant_queries)
    ood_count = len(ood_queries)
    return RetrievalMetrics(
        recall_at_1=round(_safe_divide(hits_at_1, relevant_count), 4),
        recall_at_3=round(_safe_divide(hits_at_3, relevant_count), 4),
        mean_reciprocal_rank=round(
            _safe_divide(sum(reciprocal_ranks), relevant_count),
            4,
        ),
        accepted_query_accuracy=round(
            _safe_divide(accepted_correct, accepted_total),
            4,
        ),
        out_of_domain_rejection_rate=round(
            _safe_divide(ood_rejected, ood_count),
            4,
        ),
        false_acceptance_rate=round(
            _safe_divide(ood_count - ood_rejected, ood_count),
            4,
        ),
        queries=len(queries),
        recall_at_1_ci95=wilson_interval(hits_at_1, relevant_count),
        recall_at_3_ci95=wilson_interval(hits_at_3, relevant_count),
        out_of_domain_rejection_ci95=wilson_interval(ood_rejected, ood_count),
    )


def write_report(
    metrics: RetrievalMetrics,
    path: str | Path,
    benchmark: str = "cons-trukt-precedent-retrieval-v1",
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "benchmark": benchmark,
                "metrics": metrics.to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return output_path


def format_metrics(metrics: RetrievalMetrics) -> str:
    return "\n".join(
        [
            "| Metric | Score |",
            "| --- | ---: |",
            f"| Recall@1 | {metrics.recall_at_1:.3f} "
            f"[{metrics.recall_at_1_ci95[0]:.2f}, {metrics.recall_at_1_ci95[1]:.2f}] |",
            f"| Recall@3 | {metrics.recall_at_3:.3f} "
            f"[{metrics.recall_at_3_ci95[0]:.2f}, {metrics.recall_at_3_ci95[1]:.2f}] |",
            f"| Mean reciprocal rank | {metrics.mean_reciprocal_rank:.3f} |",
            f"| Accepted-query accuracy | {metrics.accepted_query_accuracy:.3f} |",
            f"| OOD rejection | {metrics.out_of_domain_rejection_rate:.3f} |",
            f"| False acceptance | {metrics.false_acceptance_rate:.3f} |",
        ]
    )


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
