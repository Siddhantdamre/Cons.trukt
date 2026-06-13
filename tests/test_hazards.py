from __future__ import annotations

from cons_trukt.vision.hazards import HazardAnalyzer


def test_hazard_analyzer_detects_slope_and_buffer():
    report = HazardAnalyzer().analyze(
        "Site includes 18% slope with contour lines near a stream buffer."
    )

    assert report.level == "High"
    assert report.buffer is True
    assert report.flags
    assert report.density_index > 0


def test_hazard_analyzer_marks_water_only_as_medium():
    report = HazardAnalyzer().analyze("Wetland buffer and drainage channel are present.")

    assert report.level == "Medium"
    assert report.buffer is True
