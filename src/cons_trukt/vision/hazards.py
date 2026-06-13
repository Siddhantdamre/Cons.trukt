"""Ground and topographical hazard analysis."""

from __future__ import annotations

import re

from cons_trukt.schemas import HazardReport


class HazardAnalyzer:
    """Rule-based ground consequence engine for blueprint text."""

    slope_terms = ("STEEP", "INCLINE", "SLOPE", "GRADE", "CONTOUR", "TOPOGRAPH")
    buffer_terms = ("STREAM", "SURFACE WATER", "BUFFER", "WETLAND", "DRAINAGE")

    def analyze(self, text_data: str) -> HazardReport:
        normalized = text_data.upper()
        flags: list[str] = []
        level = "Low"

        density_index = self._density_index(normalized)
        slope_hit = any(term in normalized for term in self.slope_terms)
        numeric_slope_hit = bool(re.search(r"\b(?:1[5-9]|[2-9]\d)\s*%", normalized))

        if slope_hit or numeric_slope_hit:
            level = "High"
            flags.append("CRITICAL: Steep slope or topographical risk detected.")

        buffer = any(term in normalized for term in self.buffer_terms)
        if buffer:
            flags.append("ENV: Water, drainage, wetland, or stream buffer detected.")
            if level == "Low":
                level = "Medium"

        return HazardReport(level=level, flags=flags, buffer=buffer, density_index=density_index)

    def _density_index(self, normalized_text: str) -> float:
        if not normalized_text.strip():
            return 0.0
        term_count = sum(normalized_text.count(term) for term in self.slope_terms)
        percent_hits = len(re.findall(r"\b\d{1,2}\s*%", normalized_text))
        raw_score = (term_count * 0.15) + (percent_hits * 0.1)
        return round(min(raw_score, 1.0), 3)
