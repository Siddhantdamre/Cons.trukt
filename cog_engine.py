"""Compatibility adapter for the legacy cognitive engine API."""

from __future__ import annotations

from typing import Any

from cons_trukt.config import load_settings
from cons_trukt.models.factory import build_model_backend
from cons_trukt.retrieval.vector_store import ChromaPrecedentStore
from cons_trukt.schemas import HazardReport


def refine_tasks_with_history(
    blueprint_text: str,
    hazard_report: dict[str, Any] | HazardReport,
) -> dict[str, list[dict[str, Any]]]:
    settings = load_settings()
    hazard = _coerce_hazard_report(hazard_report)
    query = f"risks and permit tasks for {hazard.level} projects with {hazard.flags}"
    precedents = ChromaPrecedentStore(settings.retrieval).query(query, settings.retrieval.n_results)
    tasks = build_model_backend(settings.model).generate_tasks(blueprint_text, hazard, precedents)
    return {"tasks": [task.to_dict() for task in tasks]}


def _coerce_hazard_report(value: dict[str, Any] | HazardReport) -> HazardReport:
    if isinstance(value, HazardReport):
        return value
    return HazardReport(
        level=str(value.get("level", "Low")),
        flags=[str(item) for item in value.get("flags", [])],
        buffer=bool(value.get("buffer", False)),
        density_index=float(value.get("density_index", 0.0)),
    )
