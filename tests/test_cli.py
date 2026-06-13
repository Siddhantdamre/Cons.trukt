from __future__ import annotations

from cons_trukt.cli import build_parser, main


def test_cli_parses_public_run_interface():
    args = build_parser().parse_args(["run", "--config", "config/default.yaml", "--input", "plan.pdf"])

    assert args.command == "run"
    assert args.config.parts == ("config", "default.yaml")
    assert str(args.input_path) == "plan.pdf"


def test_cli_generate_seed_data_smoke(tmp_path):
    status = main(
        [
            "generate-seed-data",
            "--config",
            "config/default.yaml",
            "--output-dir",
            str(tmp_path),
            "--rows",
            "3",
        ]
    )

    assert status == 0
    assert (tmp_path / "slope_stability_analysis.csv").exists()
    assert (tmp_path / "industrial_standards.json").exists()
