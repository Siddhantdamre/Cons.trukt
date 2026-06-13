"""Compatibility wrapper for precedent-memory ingestion."""

from __future__ import annotations

from cons_trukt.cli import main as cli_main


def run_full_training(data_dir: str = "training_data") -> int:
    return cli_main(["ingest", "--data-dir", data_dir])


if __name__ == "__main__":
    raise SystemExit(run_full_training())
