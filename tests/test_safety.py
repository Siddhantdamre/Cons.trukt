from __future__ import annotations

from cons_trukt.models.hazard_classifier import NaiveBayesHazardClassifier
from cons_trukt.safety import SafeHazardPredictor


def _predictor() -> SafeHazardPredictor:
    model = NaiveBayesHazardClassifier().fit(
        [
            ("flat stable construction site", "Low"),
            ("floodplain elevation review", "Medium"),
            ("deep unstable trench protective system", "High"),
        ]
    )
    return SafeHazardPredictor(model)


def test_safe_predictor_escalates_out_of_domain_input():
    decision = _predictor().assess("Which laptop should accounting purchase?")

    assert decision.disposition == "escalate"
    assert decision.label is None


def test_safe_predictor_prioritizes_excavation_rule():
    decision = _predictor().assess(
        "An eight-foot trench in unstable soil lacks a protective system."
    )

    assert decision.disposition == "accept"
    assert decision.label == "High"
    assert any("LIFE SAFETY" in reason for reason in decision.reasons)


def test_safe_predictor_rejects_near_domain_translation_request():
    decision = _predictor().assess(
        "Translate the parking instructions into Spanish for the crew."
    )

    assert decision.disposition == "escalate"
    assert decision.label is None
    assert decision.intent_gate_applied is True
    assert decision.detected_intent == "translation"


def test_safe_predictor_does_not_confuse_schedule_note_with_command():
    decision = _predictor().assess(
        "Schedule notes identify an eight-foot trench in unstable soil "
        "without a protective system."
    )

    assert decision.disposition == "accept"
    assert decision.label == "High"
    assert decision.detected_intent == "hazard-condition"
