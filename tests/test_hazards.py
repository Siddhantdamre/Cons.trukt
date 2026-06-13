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


def test_hazard_analyzer_does_not_treat_negated_slope_as_high():
    report = HazardAnalyzer().analyze(
        "The existing slope does not exceed 7 percent and no wetland is present."
    )

    assert report.level == "Low"
    assert report.buffer is False


def test_hazard_analyzer_requires_slope_context_for_percentage():
    report = HazardAnalyzer().analyze("Concrete mix contains 18% recycled aggregate.")

    assert report.level == "Low"


def test_hazard_analyzer_handles_written_percent_and_surface_runoff():
    high = HazardAnalyzer().analyze("Contours indicate a 24.5 percent incline.")
    medium = HazardAnalyzer().analyze("Surface runoff collects beside material storage.")

    assert high.level == "High"
    assert medium.level == "Medium"


def test_hazard_analyzer_ignores_explicitly_out_of_scope_note():
    report = HazardAnalyzer().analyze(
        "The drainage note applies to an off-site parcel and not this project."
    )

    assert report.level == "Low"


def test_hazard_analyzer_detects_deep_unprotected_trench():
    report = HazardAnalyzer().analyze(
        "An eight-foot trench in unstable soil lacks a protective system."
    )

    assert report.level == "High"
    assert any("LIFE SAFETY" in flag for flag in report.flags)


def test_hazard_analyzer_detects_floodplain_review():
    report = HazardAnalyzer().analyze(
        "Floodplain development requires base flood elevation documentation."
    )

    assert report.level == "Medium"


def test_hazard_analyzer_detects_noncompliant_accessible_ramp():
    report = HazardAnalyzer().analyze("Accessible ramp slope is 1:10 with no landing.")

    assert report.level == "High"
    assert any("ACCESSIBILITY" in flag for flag in report.flags)
