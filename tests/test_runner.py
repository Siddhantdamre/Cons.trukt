from __future__ import annotations

from cons_trukt.config import PipelineSettings, Settings
from cons_trukt.pipeline.runner import Runner
from cons_trukt.schemas import HazardReport, KnowledgeDocument, Precedent, Task
from cons_trukt.storage.postgres import StoredTask


class FakeExtractor:
    def extract(self, path):
        return "Blueprint text with 18% slope and a detached garage."


class FakeStore:
    def query(self, question, n_results=None):
        return [Precedent(content="Slope projects often require erosion controls.", source="test")]

    def upsert_documents(self, documents):
        return len(list(documents))


class FakeBackend:
    def generate_tasks(self, blueprint_text, hazard_report, precedents):
        return [Task(wbs="03.10", name="Detached garage slab", hours=16)]


class FakeRepository:
    def __init__(self):
        self.saved: list[Task] = []

    def save_tasks(self, tasks: list[Task], hazard_report: HazardReport) -> int:
        self.saved = list(tasks)
        return len(tasks)

    def fetch_recent_tasks(self, limit: int = 10) -> list[StoredTask]:
        return []


def test_runner_applies_safety_override_and_exports_result(tmp_path):
    settings = Settings(
        pipeline=PipelineSettings(default_input=tmp_path / "plan.pdf", results_dir=tmp_path / "results"),
        project_root=tmp_path,
    )
    repository = FakeRepository()

    result = Runner(
        settings=settings,
        extractor=FakeExtractor(),
        precedent_store=FakeStore(),
        model_backend=FakeBackend(),
        task_repository=repository,
    ).run(tmp_path / "plan.pdf")

    assert len(result.tasks) == 2
    assert any("Slope Stabilization" in task.name for task in result.tasks)
    assert result.persisted_count == 2
    assert result.result_path.exists()
    assert len(repository.saved) == 2
