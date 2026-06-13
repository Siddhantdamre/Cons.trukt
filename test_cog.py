"""Compatibility smoke helper for the cognitive layer.

Pytest coverage now lives under ``tests/`` so collection does not require
runtime services such as Chroma or Ollama.
"""

from __future__ import annotations

import json
import sys

import cog_engine


def run_cog_test() -> int:
    mock_hazard_report = {
        "level": "High",
        "flags": ["CRITICAL: Steep Slope (15%+) detected", "ENV: Water Buffer detected"],
        "buffer": True,
    }
    mock_blueprint_text = """
    PROJECT: Sample House Addition.
    SITE FEATURES: Steep slope at rear of property.
    PROPOSED WORK: New detached garage and concrete retaining wall.
    UTILITIES: New plumbing for utility sink.
    """
    results = cog_engine.refine_tasks_with_history(mock_blueprint_text, mock_hazard_report)
    sys.stdout.write(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cog_test())
