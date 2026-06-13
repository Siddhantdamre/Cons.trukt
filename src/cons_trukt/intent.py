"""Intent boundary for construction hazard assessment."""

from __future__ import annotations

import re
from dataclasses import dataclass

_NON_HAZARD_PATTERNS = (
    (
        "translation",
        re.compile(r"^\s*(?:please\s+)?translate\b", re.IGNORECASE),
    ),
    (
        "summarization",
        re.compile(r"^\s*(?:please\s+)?summari[sz]e\b", re.IGNORECASE),
    ),
    (
        "document-drafting",
        re.compile(
            r"^\s*(?:please\s+)?(?:draft|write|compose)\s+"
            r"(?:a|an|the)\s+(?:email|message|memo|letter|caption|rfi|response)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "scheduling",
        re.compile(
            r"^\s*(?:please\s+)?schedule\s+(?:a|an|the|this|that)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reservation",
        re.compile(
            r"^\s*(?:please\s+)?(?:reserve|book)\s+(?:a|an|the|this|that)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "recommendation",
        re.compile(r"^\s*(?:please\s+)?recommend\b", re.IGNORECASE),
    ),
    (
        "forecasting",
        re.compile(r"^\s*(?:please\s+)?predict\b", re.IGNORECASE),
    ),
)


@dataclass(frozen=True)
class IntentAssessment:
    """Result of screening whether text asks for hazard assessment."""

    is_hazard_assessment: bool
    intent: str
    reason: str


class HazardIntentGate:
    """Detect direct workflow commands that are outside hazard classification."""

    def assess(self, text: str) -> IntentAssessment:
        for intent, pattern in _NON_HAZARD_PATTERNS:
            if pattern.search(text):
                return IntentAssessment(
                    is_hazard_assessment=False,
                    intent=intent,
                    reason=(
                        f"Detected {intent} request, not a construction-condition "
                        "hazard assessment."
                    ),
                )
        return IntentAssessment(
            is_hazard_assessment=True,
            intent="hazard-condition",
            reason="Input may describe a construction condition for hazard assessment.",
        )
