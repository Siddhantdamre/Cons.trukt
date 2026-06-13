"""Batch ingestion pipeline for precedent memory."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Iterable
from pathlib import Path

from cons_trukt.config import Settings
from cons_trukt.exceptions import IngestionError
from cons_trukt.retrieval.vector_store import PrecedentStore
from cons_trukt.schemas import IngestionStats, KnowledgeDocument
from cons_trukt.utils.logging import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """Discover, parse, chunk, and batch-upsert construction precedent datasets."""

    text_suffixes = {".txt", ".md", ".json", ".sql", ""}

    def __init__(self, settings: Settings, store: PrecedentStore) -> None:
        self.settings = settings
        self.store = store

    def ingest_directory(self, data_dir: str | Path) -> IngestionStats:
        root = Path(data_dir)
        if not root.exists():
            raise IngestionError(f"Data directory not found: {root}")

        files = [path for path in root.rglob("*") if path.is_file()]
        files_ingested = 0
        records_upserted = 0
        skipped_files = 0
        errors: list[str] = []

        for path in files:
            try:
                written = self._ingest_file(path, root)
                if written:
                    files_ingested += 1
                    records_upserted += written
                else:
                    skipped_files += 1
            except Exception as exc:
                errors.append(f"{path}: {exc}")
                logger.warning("ingestion_file_failed", path=str(path), error=str(exc))

        return IngestionStats(
            files_seen=len(files),
            files_ingested=files_ingested,
            records_upserted=records_upserted,
            skipped_files=skipped_files,
            errors=tuple(errors),
        )

    def _ingest_file(self, path: Path, root: Path) -> int:
        suffix = path.suffix.lower()
        if suffix == ".zip":
            logger.info("skipping_zip_archive", path=str(path))
            return 0
        if suffix == ".csv":
            return self._ingest_csv(path, root)
        if suffix in self.text_suffixes:
            return self._ingest_text(path, root)

        logger.info("skipping_unsupported_file", path=str(path))
        return 0

    def _ingest_csv(self, path: Path, root: Path) -> int:
        batch: list[KnowledgeDocument] = []
        total = 0
        max_rows = self.settings.retrieval.max_rows_per_csv
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row_index, row in enumerate(reader):
                if max_rows is not None and row_index >= max_rows:
                    break
                clean_row = {
                    key: value
                    for key, value in row.items()
                    if value not in (None, "", "nan")
                }
                if not clean_row:
                    continue
                content = " | ".join(f"{key}: {value}" for key, value in clean_row.items())
                batch.append(
                    KnowledgeDocument(
                        doc_id=self._stable_id(path, root, str(row_index)),
                        content=content,
                        metadata={"source": str(path), "type": "historical_permits"},
                    )
                )
                if len(batch) >= self.settings.retrieval.batch_size:
                    total += self.store.upsert_documents(batch)
                    batch = []

        if batch:
            total += self.store.upsert_documents(batch)
        logger.info("csv_ingested", path=str(path), records=total)
        return total

    def _ingest_text(self, path: Path, root: Path) -> int:
        content = path.read_text(encoding="utf-8", errors="ignore")
        chunks = list(self._chunk_text(content))
        docs = [
            KnowledgeDocument(
                doc_id=self._stable_id(path, root, str(index)),
                content=chunk,
                metadata={"source": str(path), "type": "text_archive"},
            )
            for index, chunk in enumerate(chunks)
            if chunk.strip()
        ]
        written = self.store.upsert_documents(docs)
        logger.info("text_ingested", path=str(path), records=written)
        return written

    def _chunk_text(self, content: str) -> Iterable[str]:
        size = max(1, self.settings.retrieval.text_chunk_size)
        overlap = max(0, min(self.settings.retrieval.text_chunk_overlap, size - 1))
        step = size - overlap
        for start in range(0, len(content), step):
            yield content[start : start + size]

    @staticmethod
    def _stable_id(path: Path, root: Path, suffix: str) -> str:
        try:
            relative = path.relative_to(root)
        except ValueError:
            relative = path
        digest = hashlib.sha1(f"{relative.as_posix()}:{suffix}".encode()).hexdigest()
        return digest[:24]
