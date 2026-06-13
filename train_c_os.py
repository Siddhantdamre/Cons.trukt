"""Compatibility wrapper for generated geotechnical and WBS memory ingestion."""

from __future__ import annotations

from pathlib import Path

from cons_trukt.cli import main as cli_main
from cons_trukt.seed_data import generate_seed_data


def train_from_geotechnical_data(output_dir: str = "training_data/generated") -> int:
    generate_seed_data(Path(output_dir))
    return cli_main(["ingest", "--data-dir", output_dir])


def train_from_wbs_standards(output_dir: str = "training_data/generated") -> int:
    return train_from_geotechnical_data(output_dir)


if __name__ == "__main__":
    raise SystemExit(train_from_geotechnical_data())
