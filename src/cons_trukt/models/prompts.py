"""Prompt construction and response parsing."""

from __future__ import annotations

import json
import re

from cons_trukt.exceptions import ParsingError
from cons_trukt.schemas import HazardReport, Precedent, Task


def build_task_prompt(
    blueprint_text: str,
    hazard_report: HazardReport,
    precedents: list[Precedent],
    max_blueprint_chars: int,
) -> str:
    blueprint = blueprint_text[:max_blueprint_chars].replace("{", "{{").replace("}", "}}")
    history = "\n".join(
        f"Source: {item.source}\n{item.content}" for item in precedents
    ) or "No historical precedent retrieved."
    flags = "; ".join(hazard_report.flags) or "No explicit risk flags."

    return f"""
SYSTEM: You are the C-OS Industrial Engine for construction planning.

PRIMARY BLUEPRINT DATA:
{blueprint}

GROUND RISK:
Level: {hazard_report.level}
Buffer: {hazard_report.buffer}
Density Index: {hazard_report.density_index}
Flags: {flags}

HISTORICAL PRECEDENTS:
{history}

TASK:
Extract only the construction actions physically described in the primary blueprint data.
Use historical precedents to adjust hours and professional task names, not to invent work.
Return strict JSON only using this schema:
{{"tasks": [{{"wbs": "CSI_Code", "name": "Task Name", "hours": 0}}]}}
"""


def parse_task_response(raw_content: str) -> list[Task]:
    payload = _json_loads(raw_content)
    candidate = payload.get("tasks", payload) if isinstance(payload, dict) else payload
    if isinstance(candidate, dict):
        candidate = [candidate]
    if not isinstance(candidate, list):
        raise ParsingError("Model output must be a task list or an object containing tasks.")

    tasks: list[Task] = []
    for item in candidate:
        if not isinstance(item, dict):
            raise ParsingError("Each generated task must be a JSON object.")
        tasks.append(Task.from_mapping(item))
    return tasks


def _json_loads(raw_content: str):
    cleaned = raw_content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ParsingError(f"Could not parse model JSON output: {exc}") from exc
