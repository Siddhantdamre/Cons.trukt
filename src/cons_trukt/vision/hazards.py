"""Ground and topographical hazard analysis."""

from __future__ import annotations

import re

from cons_trukt.schemas import HazardReport


class HazardAnalyzer:
    """Rule-based ground consequence engine for blueprint text."""

    strong_slope_patterns = (
        r"\bsteep\s+(?:slope|grade|incline|embankment)\b",
        r"\b(?:unstable|eroding)\s+(?:slope|embankment|bank)\b",
        r"\b(?:slope|embankment)\s+(?:failure|instability|stabilization)\b",
        r"\blandslide\b",
        r"\bretaining\s+wall\s+(?:is\s+)?required\b",
        r"\bgrade\s+is\s+steep\b",
    )
    slope_context_terms = ("SLOPE", "GRADE", "INCLINE", "CONTOUR", "TOPOGRAPH", "EMBANKMENT")
    buffer_terms = (
        "STREAM",
        "SURFACE WATER",
        "SURFACE RUNOFF",
        "BUFFER",
        "WETLAND",
        "DRAINAGE",
    )
    excavation_terms = ("TRENCH", "EXCAVATION")
    protective_system_terms = (
        "PROTECTIVE SYSTEM",
        "SHORING",
        "SHIELDED",
        "TRENCH BOX",
        "SLOPING",
        "BENCHING",
    )
    egress_terms = ("LADDER", "RAMP", "STAIRWAY", "SAFE EGRESS")
    floodplain_terms = ("FLOODPLAIN", "FLOOD HAZARD AREA", "BASE FLOOD ELEVATION", "BFE")
    stormwater_terms = (
        "SEDIMENT CONTROL",
        "EROSION CONTROL",
        "CONSTRUCTION STORMWATER",
        "STORMWATER DISCHARGE",
    )
    negation_pattern = re.compile(
        r"\b(?:NO|NOT|WITHOUT|ABSENT|NONE|NEITHER|DOES\s+NOT|DID\s+NOT)\b"
    )

    def analyze(self, text_data: str) -> HazardReport:
        normalized = " ".join(text_data.upper().split())
        flags: list[str] = []
        level = "Low"

        if self._is_out_of_scope(normalized):
            return HazardReport(level=level, flags=flags, buffer=False, density_index=0.0)

        slope_percentages = self._slope_percentages(normalized)
        numeric_slope_hit = any(value >= 15.0 for value in slope_percentages)
        explicit_slope_hit = any(
            re.search(pattern, normalized, re.IGNORECASE) for pattern in self.strong_slope_patterns
        )
        explicit_slope_hit = explicit_slope_hit and not self._negated_near(
            normalized,
            ("STEEP", "UNSTABLE", "LANDSLIDE", "STABILIZATION"),
        )

        if explicit_slope_hit or numeric_slope_hit:
            level = "High"
            flags.append("CRITICAL: Steep slope or topographical risk detected.")

        buffer = any(
            term in normalized and not self._negated_near(normalized, (term,))
            for term in self.buffer_terms
        )
        if buffer:
            flags.append("ENV: Water, drainage, wetland, or stream buffer detected.")
            if level == "Low":
                level = "Medium"

        excavation_level, excavation_flags = self._excavation_risk(normalized)
        level = self._more_severe(level, excavation_level)
        flags.extend(excavation_flags)

        accessibility_level, accessibility_flags = self._accessibility_risk(normalized)
        level = self._more_severe(level, accessibility_level)
        flags.extend(accessibility_flags)

        if self._contains_unnegated(
            normalized, self.floodplain_terms
        ) and not self._floodplain_clear(normalized):
            level = self._more_severe(level, "Medium")
            flags.append(
                "REVIEW: Floodplain conditions require elevation and flood-resistant design review."
            )

        if self._contains_unnegated(normalized, self.stormwater_terms):
            level = self._more_severe(level, "Medium")
            flags.append("ENV: Construction stormwater or erosion-control obligations detected.")

        density_index = self._density_index(
            normalized,
            slope_percentages=slope_percentages,
            explicit_slope_hit=explicit_slope_hit,
            buffer=buffer,
        )
        return HazardReport(level=level, flags=flags, buffer=buffer, density_index=density_index)

    def _excavation_risk(self, normalized_text: str) -> tuple[str, list[str]]:
        if not any(term in normalized_text for term in self.excavation_terms):
            return "Low", []

        depths = [
            float(match.group(1))
            for match in re.finditer(
                r"\b(\d+(?:\.\d+)?)\s*(?:FEET|FOOT|FT)\b",
                normalized_text,
            )
        ]
        number_words = {
            "ONE": 1.0,
            "TWO": 2.0,
            "THREE": 3.0,
            "FOUR": 4.0,
            "FIVE": 5.0,
            "SIX": 6.0,
            "SEVEN": 7.0,
            "EIGHT": 8.0,
            "NINE": 9.0,
            "TEN": 10.0,
            "TWELVE": 12.0,
            "FIFTEEN": 15.0,
            "TWENTY": 20.0,
        }
        depths.extend(
            number_words[match.group(1)]
            for match in re.finditer(
                rf"\b({'|'.join(number_words)})[-\s](?:FEET|FOOT)\b",
                normalized_text,
            )
        )
        maximum_depth = max(depths, default=0.0)
        lacks_protection = bool(
            re.search(
                r"\b(?:NO|WITHOUT|LACKS?|MISSING)\b.{0,45}"
                r"(?:PROTECTIVE SYSTEM|SHORING|TRENCH BOX|SLOPING|BENCHING)",
                normalized_text,
            )
        )
        unstable = self._contains_unnegated(
            normalized_text,
            ("UNSTABLE SOIL", "CAVE-IN", "COLLAPSE"),
        )
        lacks_egress = bool(
            re.search(
                r"\b(?:NO|WITHOUT|LACKS?|MISSING)\b.{0,35}"
                r"(?:LADDER|RAMP|STAIRWAY|SAFE EGRESS)",
                normalized_text,
            )
        )

        flags: list[str] = []
        level = "Low"
        if maximum_depth >= 5.0 and (lacks_protection or unstable):
            level = "High"
            flags.append(
                "LIFE SAFETY: Excavation at least five feet deep lacks adequate cave-in protection."
            )
        elif maximum_depth >= 5.0 and not self._contains_unnegated(
            normalized_text,
            self.protective_system_terms,
        ):
            level = "High"
            flags.append("LIFE SAFETY: Deep excavation requires protective-system verification.")

        if maximum_depth >= 4.0 and lacks_egress:
            level = "High"
            flags.append(
                "LIFE SAFETY: Excavation at least four feet deep lacks documented safe egress."
            )
        return level, flags

    def _accessibility_risk(self, normalized_text: str) -> tuple[str, list[str]]:
        if "RAMP" not in normalized_text and "ACCESSIBLE ROUTE" not in normalized_text:
            return "Low", []

        flags: list[str] = []
        ratios = [
            float(match.group(1))
            for match in re.finditer(r"\b1\s*:\s*(\d+(?:\.\d+)?)\b", normalized_text)
        ]
        too_steep = any(0 < denominator < 12 for denominator in ratios)
        lacks_landing = bool(
            re.search(
                r"\b(?:NO|WITHOUT|LACKS?|MISSING)\b.{0,30}\bLANDING\b",
                normalized_text,
            )
        )
        if too_steep:
            flags.append("ACCESSIBILITY: Ramp is steeper than the 1:12 screening threshold.")
        if lacks_landing:
            flags.append("ACCESSIBILITY: Required ramp landing is not documented.")
        return ("High" if flags else "Low"), flags

    def _slope_percentages(self, normalized_text: str) -> list[float]:
        values: list[float] = []
        pattern = r"\b(\d{1,2}(?:\.\d+)?)\s*(?:%|PERCENT\b)"
        for match in re.finditer(pattern, normalized_text):
            window = normalized_text[max(0, match.start() - 28) : match.end() + 28]
            has_slope_context = any(term in window for term in self.slope_context_terms)
            if has_slope_context and not self.negation_pattern.search(window):
                values.append(float(match.group(1)))
        return values

    @staticmethod
    def _is_out_of_scope(normalized_text: str) -> bool:
        return "OFF-SITE" in normalized_text and bool(
            re.search(r"\bNOT\s+(?:THIS|THE)\s+PROJECT\b", normalized_text)
        )

    def _negated_near(self, normalized_text: str, terms: tuple[str, ...]) -> bool:
        for term in terms:
            for match in re.finditer(rf"\b{re.escape(term)}\b", normalized_text):
                prefix = normalized_text[max(0, match.start() - 60) : match.start()]
                if self.negation_pattern.search(prefix):
                    return True
        return False

    def supports_low_risk(self, text_data: str) -> bool:
        """Return whether text explicitly documents a relevant safe condition."""
        normalized = " ".join(text_data.upper().split())
        patterns = (
            r"\bNO\b.{0,60}\b(?:STREAM|WETLAND|DRAINAGE|STORMWATER|SOIL DISTURBANCE)\b",
            r"\bOUTSIDE\b.{0,35}\b(?:FLOODPLAIN|FLOOD HAZARD AREA|MAPPED BUFFER)\b",
            r"\bCOMPLIANT\b.{0,20}\b1\s*:\s*12\b",
            r"\b1\s*:\s*12\b.{0,45}\b(?:LANDING|LANDINGS)\b",
            r"\bSHALLOW\b.{0,30}\bTRENCH\b.{0,50}\b(?:STABLE|LADDER)\b",
            r"\b(?:TRENCH|EXCAVATION)\b.{0,50}\b(?:TRENCH BOX|SHORING)\b"
            r".{0,35}\bSAFE EGRESS\b",
        )
        return any(re.search(pattern, normalized) for pattern in patterns)

    @staticmethod
    def _floodplain_clear(normalized_text: str) -> bool:
        return bool(
            re.search(
                r"\bOUTSIDE\b.{0,35}\b(?:FLOODPLAIN|FLOOD HAZARD AREA)\b",
                normalized_text,
            )
        )

    def _contains_unnegated(
        self,
        normalized_text: str,
        terms: tuple[str, ...],
    ) -> bool:
        return any(
            term in normalized_text and not self._negated_near(normalized_text, (term,))
            for term in terms
        )

    @staticmethod
    def _more_severe(left: str, right: str) -> str:
        severity = {"Low": 0, "Medium": 1, "High": 2}
        return left if severity[left] >= severity[right] else right

    def _density_index(
        self,
        normalized_text: str,
        slope_percentages: list[float],
        explicit_slope_hit: bool,
        buffer: bool,
    ) -> float:
        if not normalized_text.strip():
            return 0.0
        context_count = sum(normalized_text.count(term) for term in self.slope_context_terms)
        raw_score = min(context_count, 3) * 0.08
        raw_score += min(len(slope_percentages), 2) * 0.22
        raw_score += 0.35 if explicit_slope_hit else 0.0
        raw_score += 0.15 if buffer else 0.0
        return round(min(raw_score, 1.0), 3)
