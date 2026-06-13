"""Task persistence for PostgreSQL."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from cons_trukt.config import DatabaseSettings
from cons_trukt.exceptions import StorageError
from cons_trukt.schemas import HazardReport, Task


@dataclass(frozen=True)
class StoredTask:
    wbs_code: str
    task_name: str
    planned_hours: float
    risk_level: str


class TaskRepository(Protocol):
    def save_tasks(self, tasks: list[Task], hazard_report: HazardReport) -> int:
        """Persist tasks and return the number written."""

    def fetch_recent_tasks(self, limit: int = 10) -> list[StoredTask]:
        """Fetch recent task rows for auditing."""


class NullTaskRepository:
    """No-op repository used when no database URL is configured."""

    def save_tasks(self, tasks: list[Task], hazard_report: HazardReport) -> int:
        return 0

    def fetch_recent_tasks(self, limit: int = 10) -> list[StoredTask]:
        raise StorageError("No database URL configured. Set CONS_TRUKT_DB_URL to run audits.")


class PostgresTaskRepository:
    def __init__(self, settings: DatabaseSettings) -> None:
        if not settings.url:
            raise StorageError("Database URL is required for PostgreSQL persistence.")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", settings.table_name):
            raise StorageError(f"Invalid database table name: {settings.table_name}")
        self.settings = settings
        try:
            from sqlalchemy import create_engine
        except ImportError as exc:
            raise StorageError("sqlalchemy is required for PostgreSQL persistence.") from exc

        self.engine = create_engine(
            settings.url,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
        )

    def save_tasks(self, tasks: list[Task], hazard_report: HazardReport) -> int:
        try:
            from sqlalchemy import text
        except ImportError as exc:
            raise StorageError("sqlalchemy is required for PostgreSQL persistence.") from exc

        create_table_sql = text(
            f"""
            CREATE TABLE IF NOT EXISTS {self.settings.table_name} (
                id SERIAL PRIMARY KEY,
                wbs_code VARCHAR(50),
                task_name TEXT NOT NULL,
                planned_hours NUMERIC DEFAULT 0,
                risk_level VARCHAR(20) DEFAULT 'Low',
                environmental_buffer BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        insert_sql = text(
            f"""
            INSERT INTO {self.settings.table_name}
                (wbs_code, task_name, planned_hours, risk_level, environmental_buffer)
            VALUES
                (:wbs_code, :task_name, :planned_hours, :risk_level, :environmental_buffer)
            """
        )
        try:
            with self.engine.connect() as conn:
                conn.execute(create_table_sql)
                for task in tasks:
                    conn.execute(
                        insert_sql,
                        {
                            "wbs_code": task.wbs,
                            "task_name": task.name,
                            "planned_hours": task.hours,
                            "risk_level": hazard_report.level,
                            "environmental_buffer": hazard_report.buffer,
                        },
                    )
                conn.commit()
        except Exception as exc:
            raise StorageError(f"Could not persist generated tasks: {exc}") from exc
        return len(tasks)

    def fetch_recent_tasks(self, limit: int = 10) -> list[StoredTask]:
        try:
            from sqlalchemy import text
        except ImportError as exc:
            raise StorageError("sqlalchemy is required for PostgreSQL audits.") from exc

        query = text(
            f"""
            SELECT wbs_code, task_name, planned_hours, risk_level
            FROM {self.settings.table_name}
            ORDER BY id DESC
            LIMIT :limit
            """
        )
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(query, {"limit": limit}).mappings().all()
        except Exception as exc:
            raise StorageError(f"Could not fetch recent tasks: {exc}") from exc

        return [
            StoredTask(
                wbs_code=str(row["wbs_code"]),
                task_name=str(row["task_name"]),
                planned_hours=float(row["planned_hours"]),
                risk_level=str(row["risk_level"]),
            )
            for row in rows
        ]


def build_task_repository(settings: DatabaseSettings) -> TaskRepository:
    if not settings.url:
        return NullTaskRepository()
    return PostgresTaskRepository(settings)
