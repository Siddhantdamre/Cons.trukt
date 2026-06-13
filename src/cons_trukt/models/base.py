"""Common model backend contracts."""

from __future__ import annotations

from typing import Protocol

from cons_trukt.schemas import HazardReport, Precedent, Task


class TaskModelBackend(Protocol):
    def generate_tasks(
        self,
        blueprint_text: str,
        hazard_report: HazardReport,
        precedents: list[Precedent],
    ) -> list[Task]:
        """Generate construction tasks from blueprint text and retrieval context."""
