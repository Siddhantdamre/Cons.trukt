from __future__ import annotations

from cons_trukt.cli import build_parser, main


def test_cli_parses_public_run_interface():
    args = build_parser().parse_args(
        ["run", "--config", "config/default.yaml", "--input", "plan.pdf"]
    )

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


def test_cli_trains_and_evaluates_hazard_model(tmp_path):
    train_path = tmp_path / "train.jsonl"
    test_path = tmp_path / "test.jsonl"
    model_path = tmp_path / "model.json"
    report_path = tmp_path / "report.json"
    rows = "\n".join(
        [
            '{"id":"1","text":"flat dry pad","label":"Low","category":"flat"}',
            '{"id":"2","text":"wetland buffer","label":"Medium","category":"water"}',
            '{"id":"3","text":"steep 20% slope","label":"High","category":"slope"}',
        ]
    )
    train_path.write_text(rows, encoding="utf-8")
    test_path.write_text(rows, encoding="utf-8")

    train_status = main(
        [
            "train-hazard-model",
            "--config",
            "config/default.yaml",
            "--dataset",
            str(train_path),
            "--output",
            str(model_path),
        ]
    )
    evaluate_status = main(
        [
            "evaluate-hazards",
            "--config",
            "config/default.yaml",
            "--dataset",
            str(test_path),
            "--model",
            str(model_path),
            "--output",
            str(report_path),
        ]
    )

    assert train_status == 0
    assert evaluate_status == 0
    assert model_path.exists()
    assert report_path.exists()
