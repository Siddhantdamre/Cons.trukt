"""Scheduling manager placeholder kept as a compatibility module."""

from __future__ import annotations

from cons_trukt.utils.logging import get_logger

logger = get_logger(__name__)


def auto_reschedule(task_id: int, delay_hours: int) -> None:
    logger.info("auto_reschedule_requested", task_id=task_id, delay_hours=delay_hours)
