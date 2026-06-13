"""Typed configuration loading for Cons.trukt."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from cons_trukt.exceptions import ConfigError


@dataclass(frozen=True)
class ProcessingSettings:
    poppler_path: Path | None = None
    tesseract_cmd: Path | None = None
    ocr_workers: int = 4


@dataclass(frozen=True)
class RetrievalSettings:
    chroma_path: Path = Path("c_os_memory")
    collection_name: str = "ground_knowledge"
    n_results: int = 5
    batch_size: int = 128
    csv_chunk_size: int = 250
    max_rows_per_csv: int | None = 1000
    text_chunk_size: int = 1000
    text_chunk_overlap: int = 200


@dataclass(frozen=True)
class ModelSettings:
    backend: str = "ollama"
    ollama_model: str = "llama3.2"
    gemini_model: str = "gemini-2.0-flash"
    max_blueprint_chars: int = 12000


@dataclass(frozen=True)
class DatabaseSettings:
    url: str | None = None
    pool_size: int = 10
    max_overflow: int = 20
    table_name: str = "smart_tasks"


@dataclass(frozen=True)
class PipelineSettings:
    default_input: Path = Path("plan.pdf")
    results_dir: Path = Path("results")
    enforce_safety_overrides: bool = True


@dataclass(frozen=True)
class LoggingSettings:
    level: str = "INFO"
    structured: bool = True


@dataclass(frozen=True)
class Settings:
    processing: ProcessingSettings = ProcessingSettings()
    retrieval: RetrievalSettings = RetrievalSettings()
    model: ModelSettings = ModelSettings()
    database: DatabaseSettings = DatabaseSettings()
    pipeline: PipelineSettings = PipelineSettings()
    logging: LoggingSettings = LoggingSettings()
    project_root: Path = Path.cwd()


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load settings from YAML and environment overrides."""
    path = Path(config_path) if config_path else Path("config/default.yaml")
    raw: dict[str, Any] = {}

    if path.exists():
        raw = _read_yaml(path)
        project_root = _infer_project_root(path)
    elif config_path:
        raise ConfigError(f"Configuration file not found: {path}")
    else:
        project_root = Path.cwd()

    settings = Settings(
        processing=_processing(raw.get("processing", {})),
        retrieval=_retrieval(raw.get("retrieval", {})),
        model=_model(raw.get("model", {})),
        database=_database(raw.get("database", {})),
        pipeline=_pipeline(raw.get("pipeline", {})),
        logging=_logging(raw.get("logging", {})),
        project_root=project_root,
    )
    return _apply_env_overrides(_resolve_paths(settings))


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError("PyYAML is required to load YAML configuration files.") from exc

    with path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration root must be a mapping: {path}")
    return data


def _infer_project_root(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.parent.name == "config":
        return resolved.parent.parent
    return resolved.parent


def _path(value: Any) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _processing(raw: Any) -> ProcessingSettings:
    data = dict(raw or {})
    return ProcessingSettings(
        poppler_path=_path(data.get("poppler_path")),
        tesseract_cmd=_path(data.get("tesseract_cmd")),
        ocr_workers=int(data.get("ocr_workers", 4)),
    )


def _retrieval(raw: Any) -> RetrievalSettings:
    data = dict(raw or {})
    return RetrievalSettings(
        chroma_path=Path(str(data.get("chroma_path", "c_os_memory"))),
        collection_name=str(data.get("collection_name", "ground_knowledge")),
        n_results=int(data.get("n_results", 5)),
        batch_size=int(data.get("batch_size", 128)),
        csv_chunk_size=int(data.get("csv_chunk_size", 250)),
        max_rows_per_csv=_int_or_none(data.get("max_rows_per_csv", 1000)),
        text_chunk_size=int(data.get("text_chunk_size", 1000)),
        text_chunk_overlap=int(data.get("text_chunk_overlap", 200)),
    )


def _model(raw: Any) -> ModelSettings:
    data = dict(raw or {})
    return ModelSettings(
        backend=str(data.get("backend", "ollama")),
        ollama_model=str(data.get("ollama_model", "llama3.2")),
        gemini_model=str(data.get("gemini_model", "gemini-2.0-flash")),
        max_blueprint_chars=int(data.get("max_blueprint_chars", 12000)),
    )


def _database(raw: Any) -> DatabaseSettings:
    data = dict(raw or {})
    url = data.get("url")
    return DatabaseSettings(
        url=str(url) if url not in (None, "") else None,
        pool_size=int(data.get("pool_size", 10)),
        max_overflow=int(data.get("max_overflow", 20)),
        table_name=str(data.get("table_name", "smart_tasks")),
    )


def _pipeline(raw: Any) -> PipelineSettings:
    data = dict(raw or {})
    return PipelineSettings(
        default_input=Path(str(data.get("default_input", "plan.pdf"))),
        results_dir=Path(str(data.get("results_dir", "results"))),
        enforce_safety_overrides=bool(data.get("enforce_safety_overrides", True)),
    )


def _logging(raw: Any) -> LoggingSettings:
    data = dict(raw or {})
    return LoggingSettings(
        level=str(data.get("level", "INFO")),
        structured=bool(data.get("structured", True)),
    )


def _resolve_path(value: Path | None, root: Path) -> Path | None:
    if value is None or value.is_absolute():
        return value
    return root / value


def _resolve_paths(settings: Settings) -> Settings:
    root = settings.project_root
    return replace(
        settings,
        processing=replace(
            settings.processing,
            poppler_path=_resolve_path(settings.processing.poppler_path, root),
            tesseract_cmd=_resolve_path(settings.processing.tesseract_cmd, root),
        ),
        retrieval=replace(
            settings.retrieval,
            chroma_path=_resolve_path(settings.retrieval.chroma_path, root) or Path("c_os_memory"),
        ),
        pipeline=replace(
            settings.pipeline,
            default_input=_resolve_path(settings.pipeline.default_input, root) or Path("plan.pdf"),
            results_dir=_resolve_path(settings.pipeline.results_dir, root) or Path("results"),
        ),
    )


def _apply_env_overrides(settings: Settings) -> Settings:
    processing = settings.processing
    retrieval = settings.retrieval
    model = settings.model
    database = settings.database

    if os.getenv("CONS_TRUKT_POPPLER_PATH"):
        processing = replace(processing, poppler_path=Path(os.environ["CONS_TRUKT_POPPLER_PATH"]))
    if os.getenv("CONS_TRUKT_TESSERACT_CMD"):
        processing = replace(processing, tesseract_cmd=Path(os.environ["CONS_TRUKT_TESSERACT_CMD"]))
    if os.getenv("CONS_TRUKT_CHROMA_PATH"):
        retrieval = replace(retrieval, chroma_path=Path(os.environ["CONS_TRUKT_CHROMA_PATH"]))
    if os.getenv("CONS_TRUKT_BACKEND"):
        model = replace(model, backend=os.environ["CONS_TRUKT_BACKEND"])
    if os.getenv("CONS_TRUKT_OLLAMA_MODEL"):
        model = replace(model, ollama_model=os.environ["CONS_TRUKT_OLLAMA_MODEL"])
    if os.getenv("CONS_TRUKT_DB_URL"):
        database = replace(database, url=os.environ["CONS_TRUKT_DB_URL"])

    return replace(settings, processing=processing, retrieval=retrieval, model=model, database=database)
