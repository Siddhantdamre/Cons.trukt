"""Rule-based task output audits."""

from __future__ import annotations

from cons_trukt.schemas import AuditReport
from cons_trukt.storage.postgres import StoredTask, TaskRepository


def audit_recent_tasks(repository: TaskRepository, limit: int = 10) -> AuditReport:
    rows = repository.fetch_recent_tasks(limit=limit)
    return audit_task_rows(rows)


def audit_task_rows(rows: list[StoredTask]) -> AuditReport:
    passes: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    if not rows:
        errors.append("No recent tasks found to audit.")
        return AuditReport(passes=tuple(passes), warnings=tuple(warnings), errors=tuple(errors))

    is_high_risk = any(row.risk_level == "High" for row in rows)
    has_stabilization = any(
        _contains_any(row.task_name, ("slope", "stabilization", "erosion")) for row in rows
    )
    if is_high_risk and not has_stabilization:
        errors.append("High risk detected but no slope stabilization task found.")
    else:
        passes.append("Ground condition risk has matching mitigation coverage.")

    zero_hour_count = sum(1 for row in rows if row.planned_hours <= 0)
    if zero_hour_count:
        errors.append(f"Found {zero_hour_count} tasks with non-positive planned hours.")
    else:
        passes.append("All audited tasks have positive planned-hour estimates.")

    generic_wbs_count = sum(1 for row in rows if row.wbs_code == "0.0")
    if generic_wbs_count:
        warnings.append(f"Found {generic_wbs_count} tasks with generic WBS code 0.0.")

    return AuditReport(passes=tuple(passes), warnings=tuple(warnings), errors=tuple(errors))


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(needle in lowered for needle in needles)
