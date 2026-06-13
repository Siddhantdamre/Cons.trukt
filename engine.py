"""Compatibility wrapper for the optional Gemini blueprint parser."""

from __future__ import annotations

from pathlib import Path

from cons_trukt.config import load_settings
from cons_trukt.models.gemini_backend import parse_blueprint_with_gemini


def parse_blueprint(file_path: str | Path) -> str:
    settings = load_settings()
    return parse_blueprint_with_gemini(file_path, settings.model)
