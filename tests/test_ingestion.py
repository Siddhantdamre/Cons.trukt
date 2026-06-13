from __future__ import annotations

from cons_trukt.config import RetrievalSettings, Settings
from cons_trukt.pipeline.processor import DataProcessor
from cons_trukt.retrieval.vector_store import InMemoryPrecedentStore


def test_data_processor_recurses_and_batches_csv_and_text(tmp_path):
    data_dir = tmp_path / "training_data"
    nested = data_dir / "archive"
    nested.mkdir(parents=True)
    (data_dir / "permits.csv").write_text("id,name\n1,Garage\n2,Deck\n", encoding="utf-8")
    (nested / "notes.md").write_text("slope buffer drainage", encoding="utf-8")
    (data_dir / "archive.zip").write_bytes(b"zip")

    settings = Settings(
        retrieval=RetrievalSettings(
            batch_size=2,
            max_rows_per_csv=None,
            text_chunk_size=8,
            text_chunk_overlap=2,
        ),
        project_root=tmp_path,
    )
    store = InMemoryPrecedentStore(documents=[])

    stats = DataProcessor(settings, store).ingest_directory(data_dir)

    assert stats.files_seen == 3
    assert stats.files_ingested == 2
    assert stats.skipped_files == 1
    assert stats.records_upserted == len(store.documents)
    assert {doc.metadata["type"] for doc in store.documents} == {
        "historical_permits",
        "text_archive",
    }


def test_data_processor_stable_ids_are_deterministic(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    path = data_dir / "permits.csv"

    first = DataProcessor._stable_id(path, data_dir, "0")
    second = DataProcessor._stable_id(path, data_dir, "0")

    assert first == second
