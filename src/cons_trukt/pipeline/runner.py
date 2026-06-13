"""End-to-end pipeline runner."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from cons_trukt.config import Settings
from cons_trukt.models.base import TaskModelBackend
from cons_trukt.models.factory import build_model_backend
from cons_trukt.processing.pdf_extractor import PDFTextExtractor
from cons_trukt.retrieval.vector_store import ChromaPrecedentStore, PrecedentStore
from cons_trukt.schemas import HazardReport, PipelineResult, Precedent, Task
from cons_trukt.storage.postgres import TaskRepository, build_task_repository
from cons_trukt.utils.logging import get_logger
from cons_trukt.vision.hazards import HazardAnalyzer

logger = get_logger(__name__)


class Runner:
    """Coordinates extraction, hazard analysis, retrieval, model reasoning, and persistence."""

    def __init__(
        self,
        settings: Settings,
        extractor: PDFTextExtractor | None = None,
        hazard_analyzer: HazardAnalyzer | None = None,
        precedent_store: PrecedentStore | None = None,
        model_backend: TaskModelBackend | None = None,
        task_repository: TaskRepository | None = None,
    ) -> None:
        self.settings = settings
        self.extractor = extractor or PDFTextExtractor(settings.processing)
        self.hazard_analyzer = hazard_analyzer or HazardAnalyzer()
        self.precedent_store = precedent_store or ChromaPrecedentStore(settings.retrieval)
        self.model_backend = model_backend or build_model_backend(settings.model)
        self.task_repository = task_repository or build_task_repository(settings.database)

    def run(self, input_path: str | Path | None = None) -> PipelineResult:
        path = Path(input_path) if input_path else self.settings.pipeline.default_input
        logger.info("pipeline_started", input_path=str(path))

        raw_text = self.extractor.extract(path)
        hazard_report = self.hazard_analyzer.analyze(raw_text)
        precedents = self._retrieve_precedents(hazard_report)
        tasks = self.model_backend.generate_tasks(raw_text, hazard_report, precedents)
        tasks = self._apply_safety_overrides(tasks, hazard_report)
        persisted_count = self.task_repository.save_tasks(tasks, hazard_report)
        result_path = self._export_result(path, hazard_report, tasks, precedents, persisted_count)

        logger.info(
            "pipeline_completed",
            input_path=str(path),
            tasks=len(tasks),
            persisted_count=persisted_count,
            result_path=str(result_path),
        )
        return PipelineResult(
            input_path=path,
            hazard=hazard_report,
            tasks=tasks,
            precedents=precedents,
            persisted_count=persisted_count,
            result_path=result_path,
        )

    def _retrieve_precedents(self, hazard_report: HazardReport) -> list[Precedent]:
        question = (
            f"risks and permit tasks for {hazard_report.level} projects "
            f"with flags {', '.join(hazard_report.flags)}"
        )
        return self.precedent_store.query(question, n_results=self.settings.retrieval.n_results)

    def _apply_safety_overrides(self, tasks: list[Task], hazard_report: HazardReport) -> list[Task]:
        if not self.settings.pipeline.enforce_safety_overrides:
            return tasks
        if hazard_report.level != "High":
            return tasks
        if any(_contains_any(task.name, ("slope", "stabilization", "erosion")) for task in tasks):
            return tasks
        return tasks + [Task(wbs="02.50", name="Slope Stabilization & Erosion Control", hours=40.0)]

    def _export_result(
        self,
        input_path: Path,
        hazard_report: HazardReport,
        tasks: list[Task],
        precedents: list[Precedent],
        persisted_count: int,
    ) -> Path:
        results_dir = self.settings.pipeline.results_dir
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = results_dir / f"{timestamp}_{input_path.stem}_tasks.json"
        payload = {
            "input_path": str(input_path),
            "hazard": hazard_report.to_dict(),
            "tasks": [task.to_dict() for task in tasks],
            "precedents": [precedent.to_dict() for precedent in precedents],
            "persisted_count": persisted_count,
            "generated_at": timestamp,
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(needle in lowered for needle in needles)
