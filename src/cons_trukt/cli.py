"""Command-line interface for Cons.trukt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cons_trukt.audit import audit_recent_tasks
from cons_trukt.config import Settings, load_settings
from cons_trukt.evaluation import (
    HybridHazardPredictor,
    LearnedHazardPredictor,
    RuleHazardPredictor,
    evaluate_predictor,
    evaluate_safe_predictor,
    format_evaluation_summary,
    format_selective_summary,
    load_hazard_examples,
    load_ood_examples,
    train_hazard_classifier,
    write_evaluation_report,
    write_selective_evaluation_report,
)
from cons_trukt.exceptions import ConsTruktError
from cons_trukt.models.hazard_classifier import NaiveBayesHazardClassifier
from cons_trukt.pipeline.processor import DataProcessor
from cons_trukt.pipeline.runner import Runner
from cons_trukt.retrieval.evaluation import (
    evaluate_retrieval,
    format_metrics,
    load_queries,
    write_report,
)
from cons_trukt.retrieval.tfidf_store import TfidfPrecedentStore, load_corpus
from cons_trukt.retrieval.vector_store import ChromaPrecedentStore
from cons_trukt.safety import SafeHazardPredictor
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

    train_parser = subparsers.add_parser(
        "train-hazard-model",
        help="Train the dependency-free hazard severity baseline.",
    )
    _add_config_arg(train_parser)
    train_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("benchmarks/hazard_v1/train.jsonl"),
    )
    train_parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/hazard_nb_v1.json"),
    )
    train_parser.add_argument("--alpha", type=float, default=1.0)

    evaluate_parser = subparsers.add_parser(
        "evaluate-hazards",
        help="Evaluate rule, learned, and hybrid hazard classifiers.",
    )
    _add_config_arg(evaluate_parser)
    evaluate_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("benchmarks/hazard_v1/test.jsonl"),
    )
    evaluate_parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/hazard_nb_v1.json"),
    )
    evaluate_parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/hazard_v1/evaluation.json"),
    )

    validate_parser = subparsers.add_parser(
        "validate-hazards",
        help="Measure selective accuracy, high-risk recall, and OOD rejection.",
    )
    _add_config_arg(validate_parser)
    validate_parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("benchmarks/hazard_v2/test.jsonl"),
    )
    validate_parser.add_argument(
        "--ood-dataset",
        type=Path,
        default=Path("benchmarks/hazard_v2/ood.jsonl"),
    )
    validate_parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/hazard_nb_v2.json"),
    )
    validate_parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/hazard_v2/selective_evaluation.json"),
    )

    assess_parser = subparsers.add_parser(
        "assess-hazard",
        help="Assess one condition with uncertainty and escalation.",
    )
    _add_config_arg(assess_parser)
    assess_parser.add_argument("condition")
    assess_parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/hazard_nb_v2.json"),
    )

    fit_retrieval_parser = subparsers.add_parser(
        "fit-precedent-index",
        help="Fit a dependency-free local TF-IDF precedent index.",
    )
    _add_config_arg(fit_retrieval_parser)
    fit_retrieval_parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("benchmarks/retrieval_v1/corpus.jsonl"),
    )
    fit_retrieval_parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/precedent_tfidf_v1.json"),
    )

    evaluate_retrieval_parser = subparsers.add_parser(
        "evaluate-retrieval",
        help="Evaluate the local precedent index on frozen queries.",
    )
    _add_config_arg(evaluate_retrieval_parser)
    evaluate_retrieval_parser.add_argument(
        "--queries",
        type=Path,
        default=Path("benchmarks/retrieval_v1/queries.jsonl"),
    )
    evaluate_retrieval_parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/precedent_tfidf_v1.json"),
    )
    evaluate_retrieval_parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/retrieval_v1/evaluation.json"),
    )

    offline_query_parser = subparsers.add_parser(
        "query-offline",
        help="Query a fitted local precedent index without Chroma.",
    )
    _add_config_arg(offline_query_parser)
    offline_query_parser.add_argument("question")
    offline_query_parser.add_argument(
        "--model",
        type=Path,
        default=Path("artifacts/precedent_tfidf_v1.json"),
    )
    offline_query_parser.add_argument("--limit", type=int, default=3)
    offline_query_parser.add_argument(
        "--unsafe",
        action="store_true",
        help="Return raw rankings even when confidence thresholds fail.",
    )

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
        audit_report = audit_recent_tasks(repository, limit=args.limit)
        for item in audit_report.passes:
            sys.stdout.write(f"PASS: {item}\n")
        for item in audit_report.warnings:
            sys.stdout.write(f"WARNING: {item}\n")
        for item in audit_report.errors:
            sys.stdout.write(f"FAIL: {item}\n")
        return 0 if audit_report.ok else 2

    if args.command == "generate-seed-data":
        slope_path, standards_path = generate_seed_data(args.output_dir, rows=args.rows)
        sys.stdout.write(f"Created {slope_path}\nCreated {standards_path}\n")
        return 0

    if args.command == "train-hazard-model":
        model = train_hazard_classifier(args.dataset, args.output, alpha=args.alpha)
        sys.stdout.write(
            f"Trained hazard classifier on {sum(model.class_counts.values())} examples: "
            f"{args.output}\n"
        )
        return 0

    if args.command == "evaluate-hazards":
        examples = load_hazard_examples(args.dataset)
        model = NaiveBayesHazardClassifier.load(args.model)
        reports = [
            evaluate_predictor(
                RuleHazardPredictor(),
                examples,
                model_name="rule",
                dataset_name=str(args.dataset),
            ),
            evaluate_predictor(
                LearnedHazardPredictor(model),
                examples,
                model_name="naive_bayes",
                dataset_name=str(args.dataset),
            ),
            evaluate_predictor(
                HybridHazardPredictor(model),
                examples,
                model_name="hybrid",
                dataset_name=str(args.dataset),
            ),
        ]
        output_path = write_evaluation_report(reports, args.output)
        sys.stdout.write(f"{format_evaluation_summary(reports)}\n\nSaved {output_path}\n")
        return 0

    if args.command == "validate-hazards":
        model = NaiveBayesHazardClassifier.load(args.model)
        selective_report = evaluate_safe_predictor(
            SafeHazardPredictor(model),
            load_hazard_examples(args.dataset),
            load_ood_examples(args.ood_dataset),
            dataset_name=str(args.dataset),
        )
        output_path = write_selective_evaluation_report(
            selective_report,
            args.output,
        )
        sys.stdout.write(f"{format_selective_summary(selective_report)}\n\nSaved {output_path}\n")
        return 0

    if args.command == "assess-hazard":
        model = NaiveBayesHazardClassifier.load(args.model)
        hazard_decision = SafeHazardPredictor(model).assess(args.condition)
        sys.stdout.write(json.dumps(hazard_decision.to_dict(), indent=2))
        sys.stdout.write("\n")
        return 0 if hazard_decision.disposition == "accept" else 2

    if args.command == "fit-precedent-index":
        documents = load_corpus(args.corpus)
        TfidfPrecedentStore(documents).save(args.output)
        sys.stdout.write(
            f"Fitted TF-IDF precedent index on {len(documents)} documents: {args.output}\n"
        )
        return 0

    if args.command == "evaluate-retrieval":
        offline_store = TfidfPrecedentStore.load(args.model)
        metrics = evaluate_retrieval(
            offline_store,
            load_queries(args.queries),
        )
        benchmark_name = (
            "cons-trukt-precedent-retrieval-v2"
            if "v2" in str(args.queries).lower()
            else "cons-trukt-precedent-retrieval-v1"
        )
        output_path = write_report(
            metrics,
            args.output,
            benchmark=benchmark_name,
        )
        sys.stdout.write(f"{format_metrics(metrics)}\n\nSaved {output_path}\n")
        return 0

    if args.command == "query-offline":
        offline_store = TfidfPrecedentStore.load(args.model)
        if not args.unsafe:
            retrieval_decision = offline_store.query_safe(
                args.question,
                n_results=args.limit,
            )
            sys.stdout.write(json.dumps(retrieval_decision.to_dict(), indent=2))
            sys.stdout.write("\n")
            return 0 if retrieval_decision.accepted else 2
        for index, precedent in enumerate(
            offline_store.query(args.question, n_results=args.limit),
            start=1,
        ):
            snippet = precedent.content.replace("\n", " ")[:240]
            score = precedent.score if precedent.score is not None else 0.0
            sys.stdout.write(f"[{index}] {score:.4f} {precedent.source}: {snippet}\n")
        return 0

    raise ConsTruktError(f"Unsupported command: {args.command}")


def _add_config_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, default=Path("config/default.yaml"))


if __name__ == "__main__":
    raise SystemExit(main())
