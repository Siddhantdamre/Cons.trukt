from __future__ import annotations

import pytest

from cons_trukt.exceptions import ParsingError
from cons_trukt.models.prompts import build_task_prompt, parse_task_response
from cons_trukt.schemas import HazardReport, Precedent


def test_prompt_keeps_retrieval_context_separate_from_primary_data():
    prompt = build_task_prompt(
        blueprint_text="Garage with {braces}",
        hazard_report=HazardReport(level="High", flags=["Slope"], buffer=False),
        precedents=[Precedent(content="Historical permit pattern", source="permit.csv")],
        max_blueprint_chars=100,
    )

    assert "PRIMARY BLUEPRINT DATA" in prompt
    assert "HISTORICAL PRECEDENTS" in prompt
    assert "permit.csv" in prompt


def test_parse_task_response_accepts_strict_json():
    tasks = parse_task_response('{"tasks": [{"wbs": "02.10", "name": "Excavate", "hours": 12}]}')

    assert len(tasks) == 1
    assert tasks[0].wbs == "02.10"
    assert tasks[0].hours == 12


def test_parse_task_response_rejects_invalid_task():
    with pytest.raises(ParsingError):
        parse_task_response('{"tasks": [{"wbs": "02.10", "hours": "nope"}]}')
