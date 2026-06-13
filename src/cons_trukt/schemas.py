"""Typed data contracts used across the pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cons_trukt.exceptions import ParsingError


@dataclass(frozen=True)
class HazardReport:
    level: str
    flags: list[str] = field(default_factory=list)
    buffer: bool = False
    density_index: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Precedent:
    content: str
    source: str = "unknown"
    kind: str = "historical_permits"
    score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    content: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Task:
    wbs: str
    name: str
    hours: float

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Task":
        wbs = str(data.get("wbs") or data.get("wbs_code") or "0.0").strip()
        name = str(data.get("name") or data.get("task_name") or "").strip()
        if not name:
            raise ParsingError("Task is missing a non-empty name.")
        raw_hours = data.get("hours", data.get("planned_hours", data.get("estimated_hours", 0)))
        try:
            hours = float(raw_hours)
        except (TypeError, ValueError) as exc:
            raise ParsingError(f"Task has invalid hours value: {raw_hours!r}") from exc
        if hours < 0:
            raise ParsingError("Task hours cannot be negative.")
        return cls(wbs=wbs or "0.0", name=name, hours=hours)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PipelineResult:
    input_path: Path
    hazard: HazardReport
    tasks: list[Task]
    precedents: list[Precedent]
    persisted_count: int
    result_path: Path


@dataclass(frozen=True)
class IngestionStats:
    files_seen: int = 0
    files_ingested: int = 0
    records_upserted: int = 0
    skipped_files: int = 0
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditReport:
    passes: tuple[str, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors
