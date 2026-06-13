from __future__ import annotations

from cons_trukt.audit import audit_task_rows
from cons_trukt.storage.postgres import StoredTask


def test_audit_flags_high_risk_without_stabilization():
    report = audit_task_rows(
        [
            StoredTask(
                wbs_code="03.10",
                task_name="Concrete slab",
                planned_hours=12,
                risk_level="High",
            )
        ]
    )

    assert not report.ok
    assert any("High risk" in error for error in report.errors)


def test_audit_passes_with_mitigation_and_positive_hours():
    report = audit_task_rows(
        [
            StoredTask(
                wbs_code="02.50",
                task_name="Slope Stabilization",
                planned_hours=40,
                risk_level="High",
            )
        ]
    )

    assert report.ok
    assert report.passes
