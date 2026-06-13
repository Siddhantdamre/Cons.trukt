from __future__ import annotations

from pathlib import Path

from cons_trukt.config import load_settings


def test_load_settings_resolves_paths_and_env_override(tmp_path, monkeypatch):
    project = tmp_path / "project"
    config_dir = project / "config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "default.yaml"
    config_path.write_text(
        """
retrieval:
  chroma_path: memory
database:
  url: null
pipeline:
  default_input: plan.pdf
  results_dir: outputs
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CONS_TRUKT_DB_URL", "postgresql://example/db")

    settings = load_settings(config_path)

    assert settings.project_root == project
    assert settings.retrieval.chroma_path == project / "memory"
    assert settings.pipeline.default_input == project / "plan.pdf"
    assert settings.pipeline.results_dir == project / "outputs"
    assert settings.database.url == "postgresql://example/db"


def test_default_settings_load_from_repo_config():
    settings = load_settings(Path("config/default.yaml"))

    assert settings.model.backend == "ollama"
    assert settings.model.ollama_model == "llama3.2"
    assert settings.retrieval.collection_name == "ground_knowledge"
