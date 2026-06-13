"""Ollama local model backend."""

from __future__ import annotations

from cons_trukt.config import ModelSettings
from cons_trukt.exceptions import ModelBackendError, ParsingError
from cons_trukt.models.prompts import build_task_prompt, parse_task_response
from cons_trukt.schemas import HazardReport, Precedent, Task


class OllamaTaskBackend:
    def __init__(self, settings: ModelSettings) -> None:
        self.settings = settings

    def generate_tasks(
        self,
        blueprint_text: str,
        hazard_report: HazardReport,
        precedents: list[Precedent],
    ) -> list[Task]:
        try:
            import ollama
        except ImportError as exc:
            raise ModelBackendError("ollama is required for the local model backend.") from exc

        prompt = build_task_prompt(
            blueprint_text=blueprint_text,
            hazard_report=hazard_report,
            precedents=precedents,
            max_blueprint_chars=self.settings.max_blueprint_chars,
        )
        try:
            response = ollama.chat(
                model=self.settings.ollama_model,
                format="json",
                messages=[{"role": "user", "content": prompt}],
            )
            content = response["message"]["content"]
            return parse_task_response(str(content))
        except ParsingError:
            raise
        except Exception as exc:
            raise ModelBackendError(f"Ollama task generation failed: {exc}") from exc
