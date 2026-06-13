"""Command-line interface for Cons.trukt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cons_trukt.audit import audit_recent_tasks
from cons_trukt.config import Settings, load_settings
from cons_trukt.exceptions import ConsTruktError
from cons_trukt.pipeline.processor import DataProcessor
from cons_trukt.pipeline.runner import Runner
from cons_trukt.retrieval.vector_store import ChromaPrecedentStore
from cons_trukt.seed_data import generate_seed_data
from cons_trukt.storage.postgres import build_task_repository
from cons_trukt.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cons_trukt", description="Cons.trukt pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the blueprint-to-task pipeline.")
    _add_config_arg(run_parser)
    run_parser.add_argument("--input", dest="input_path", type=Path, default=None)

    ingest_parser = subparsers.add_parser("ingest", help="Build or refresh precedent memory.")
    _add_config_arg(ingest_parser)
    ingest_parser.add_argument("--data-dir", type=Path, default=Path("training_data"))

    query_parser = subparsers.add_parser("query", help="Query precedent memory.")
    _add_config_arg(query_parser)
    query_parser.add_argument("question")
    query_parser.add_argument("--limit", type=int, default=None)

    audit_parser = subparsers.add_parser("audit", help="Audit recent generated tasks.")
    _add_config_arg(audit_parser)
    audit_parser.add_argument("--limit", type=int, default=10)

    seed_parser = subparsers.add_parser("generate-seed-data", help="Generate synthetic seed data.")
    _add_config_arg(seed_parser)
    seed_parser.add_argument("--output-dir", type=Path, default=Path("."))
    seed_parser.add_argument("--rows", type=int, default=1000)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        settings = load_settings(args.config)
        configure_logging(settings.logging.level, settings.logging.structured)
        return _dispatch(args, settings)
    except ConsTruktError as exc:
        logger.error("command_failed", error=str(exc))
        sys.stderr.write(f"Error: {exc}\n")
        return 1


def _dispatch(args: argparse.Namespace, settings: Settings) -> int:
    if args.command == "run":
        result = Runner(settings).run(args.input_path)
        sys.stdout.write(f"Generated {len(result.tasks)} tasks: {result.result_path}\n")
        return 0

    if args.command == "ingest":
        store = ChromaPrecedentStore(settings.retrieval)
        stats = DataProcessor(settings, store).ingest_directory(args.data_dir)
        sys.stdout.write(
            "Ingested "
            f"{stats.records_upserted} records from {stats.files_ingested} files "
            f"({stats.skipped_files} skipped, {len(stats.errors)} errors).\n"
        )
        return 0 if not stats.errors else 2

    if args.command == "query":
        store = ChromaPrecedentStore(settings.retrieval)
        precedents = store.query(args.question, n_results=args.limit)
        for index, precedent in enumerate(precedents, start=1):
            snippet = precedent.content.replace("\n", " ")[:240]
            sys.stdout.write(f"[{index}] {precedent.source}: {snippet}\n")
        return 0

    if args.command == "audit":
        repository = build_task_repository(settings.database)
        report = audit_recent_tasks(repository, limit=args.limit)
        for item in report.passes:
            sys.stdout.write(f"PASS: {item}\n")
        for item in report.warnings:
            sys.stdout.write(f"WARNING: {item}\n")
        for item in report.errors:
            sys.stdout.write(f"FAIL: {item}\n")
        return 0 if report.ok else 2

    if args.command == "generate-seed-data":
        slope_path, standards_path = generate_seed_data(args.output_dir, rows=args.rows)
        sys.stdout.write(f"Created {slope_path}\nCreated {standards_path}\n")
        return 0

    raise ConsTruktError(f"Unsupported command: {args.command}")


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, default=Path("config/default.yaml"))


if __name__ == "__main__":
    raise SystemExit(main())
