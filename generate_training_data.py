"""Compatibility wrapper for synthetic seed-data generation."""

from __future__ import annotations

from cons_trukt.cli import main as cli_main


def create_slope_dataset(output_dir: str = ".") -> int:
    return cli_main(["generate-seed-data", "--output-dir", output_dir])


def create_wbs_standards(output_dir: str = ".") -> int:
    return cli_main(["generate-seed-data", "--output-dir", output_dir])


if __name__ == "__main__":
    raise SystemExit(cli_main(["generate-seed-data", "--output-dir", "."]))
