"""Optional Gemini model backend."""

from __future__ import annotations

import os
from pathlib import Path

from cons_trukt.config import ModelSettings
from cons_trukt.exceptions import ModelBackendError, ParsingError
from cons_trukt.models.prompts import build_task_prompt, parse_task_response
from cons_trukt.schemas import HazardReport, Precedent, Task


class GeminiTaskBackend:
    def __init__(self, settings: ModelSettings, api_key: str | None = None) -> None:
        self.settings = settings
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

    def generate_tasks(
        self,
        blueprint_text: str,
        hazard_report: HazardReport,
        precedents: list[Precedent],
    ) -> list[Task]:
        if not self.api_key:
            raise ModelBackendError("GOOGLE_API_KEY is required when model.backend is gemini.")
        try:
            from google import genai
        except ImportError as exc:
            raise ModelBackendError("google-genai is required for the Gemini backend.") from exc

        prompt = build_task_prompt(
            blueprint_text=blueprint_text,
            hazard_report=hazard_report,
            precedents=precedents,
            max_blueprint_chars=self.settings.max_blueprint_chars,
        )
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            return parse_task_response(str(response.text))
        except ParsingError:
            raise
        except Exception as exc:
            raise ModelBackendError(f"Gemini task generation failed: {exc}") from exc


def parse_blueprint_with_gemini(file_path: str | Path, settings: ModelSettings) -> str:
    """Compatibility helper for the old Gemini blueprint parsing prototype."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ModelBackendError("GOOGLE_API_KEY is required for Gemini blueprint parsing.")
    try:
        from google import genai
    except ImportError as exc:
        raise ModelBackendError("google-genai is required for Gemini blueprint parsing.") from exc

    client = genai.Client(api_key=api_key)
    document = client.files.upload(path=str(file_path))
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=[document, "Extract the Bill of Quantities. Format as JSON with WBS codes."],
        config={"response_mime_type": "application/json"},
    )
    return str(response.text)
