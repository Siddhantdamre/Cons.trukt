"""Selective hazard decisions with explicit uncertainty and escalation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from cons_trukt.intent import HazardIntentGate
from cons_trukt.models.hazard_classifier import NaiveBayesHazardClassifier
from cons_trukt.vision.hazards import HazardAnalyzer


@dataclass(frozen=True)
class HazardDecision:
    label: str | None
    disposition: str
    confidence: float
    reasons: tuple[str, ...]
    probabilities: dict[str, float]
    known_token_ratio: float
    intent_gate_applied: bool = False
    detected_intent: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SafeHazardPredictor:
    """Prefer deterministic safety rules and abstain on weak or unfamiliar input."""

    def __init__(
        self,
        model: NaiveBayesHazardClassifier,
        minimum_confidence: float = 0.72,
        minimum_known_token_ratio: float = 0.3,
    ) -> None:
        self.model = model
        self.rules = HazardAnalyzer()
        self.intent_gate = HazardIntentGate()
        self.minimum_confidence = minimum_confidence
        self.minimum_known_token_ratio = minimum_known_token_ratio

    def assess(self, text: str) -> HazardDecision:
        if not text.strip():
            return self._escalate("No project condition text was provided.")

        intent = self.intent_gate.assess(text)
        if not intent.is_hazard_assessment:
            return self._escalate(
                intent.reason,
                intent_gate_applied=True,
                detected_intent=intent.intent,
            )

        rule_report = self.rules.analyze(text)
        learned = self.model.predict(text)
        if rule_report.flags:
            return HazardDecision(
                label=rule_report.level,
                disposition="accept",
                confidence=round(max(0.92, learned.probabilities[rule_report.level]), 6),
                reasons=tuple(rule_report.flags),
                probabilities=learned.probabilities,
                known_token_ratio=learned.known_token_ratio,
                intent_gate_applied=True,
                detected_intent=intent.intent,
            )

        if self.rules.supports_low_risk(text):
            return HazardDecision(
                label="Low",
                disposition="accept",
                confidence=round(max(0.9, learned.probabilities["Low"]), 6),
                reasons=("Explicit safe or non-applicable condition documented.",),
                probabilities=learned.probabilities,
                known_token_ratio=learned.known_token_ratio,
                intent_gate_applied=True,
                detected_intent=intent.intent,
            )

        if learned.known_token_ratio < self.minimum_known_token_ratio:
            return self._escalate(
                "Input is outside the trained construction-hazard vocabulary.",
                learned.probabilities,
                learned.known_token_ratio,
                intent_gate_applied=True,
                detected_intent=intent.intent,
            )
        if learned.confidence < self.minimum_confidence:
            return self._escalate(
                "Model confidence is below the production acceptance threshold.",
                learned.probabilities,
                learned.known_token_ratio,
                intent_gate_applied=True,
                detected_intent=intent.intent,
            )

        return HazardDecision(
            label=learned.label,
            disposition="accept",
            confidence=learned.confidence,
            reasons=("Assessment supported by the fitted hazard classifier.",),
            probabilities=learned.probabilities,
            known_token_ratio=learned.known_token_ratio,
            intent_gate_applied=True,
            detected_intent=intent.intent,
        )

    @staticmethod
    def _escalate(
        reason: str,
        probabilities: dict[str, float] | None = None,
        known_token_ratio: float = 0.0,
        intent_gate_applied: bool = False,
        detected_intent: str = "",
    ) -> HazardDecision:
        return HazardDecision(
            label=None,
            disposition="escalate",
            confidence=0.0,
            reasons=(reason,),
            probabilities=probabilities or {},
            known_token_ratio=known_token_ratio,
            intent_gate_applied=intent_gate_applied,
            detected_intent=detected_intent,
        )
