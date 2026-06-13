"""Reproducible evaluation utilities for construction hazard classification."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from cons_trukt.models.hazard_classifier import LABELS, NaiveBayesHazardClassifier
from cons_trukt.safety import SafeHazardPredictor
from cons_trukt.statistics import Interval, wilson_interval
from cons_trukt.vision.hazards import HazardAnalyzer


@dataclass(frozen=True)
class HazardExample:
    example_id: str
    text: str
    label: str
    category: str


@dataclass(frozen=True)
class ClassMetrics:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass(frozen=True)
class EvaluationReport:
    model: str
    dataset: str
    examples: int
    accuracy: float
    macro_f1: float
    per_class: dict[str, ClassMetrics]
    confusion_matrix: dict[str, dict[str, int]]
    errors: tuple[dict[str, str], ...]
    accuracy_ci95: Interval = (0.0, 0.0)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["accuracy_ci95"] = list(self.accuracy_ci95)
        return payload


@dataclass(frozen=True)
class SelectiveEvaluationReport:
    dataset: str
    in_domain_examples: int
    out_of_domain_examples: int
    coverage: float
    accepted_accuracy: float
    escalation_rate: float
    high_risk_detection_rate: float
    unsafe_false_low_rate: float
    out_of_domain_rejection_rate: float
    errors: tuple[dict[str, str], ...]
    accepted_accuracy_ci95: Interval = (0.0, 0.0)
    high_risk_detection_ci95: Interval = (0.0, 0.0)
    out_of_domain_rejection_ci95: Interval = (0.0, 0.0)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["errors"] = list(self.errors)
        payload["accepted_accuracy_ci95"] = list(self.accepted_accuracy_ci95)
        payload["high_risk_detection_ci95"] = list(self.high_risk_detection_ci95)
        payload["out_of_domain_rejection_ci95"] = list(self.out_of_domain_rejection_ci95)
        return payload


class HazardPredictor(Protocol):
    def predict_label(self, text: str) -> str:
        """Predict one of Low, Medium, or High."""


class RuleHazardPredictor:
    def __init__(self) -> None:
        self.analyzer = HazardAnalyzer()

    def predict_label(self, text: str) -> str:
        return self.analyzer.analyze(text).level


class LearnedHazardPredictor:
    def __init__(self, model: NaiveBayesHazardClassifier) -> None:
        self.model = model

    def predict_label(self, text: str) -> str:
        return self.model.predict(text).label


class HybridHazardPredictor:
    """Combine deterministic safety rules with a learned lexical baseline."""

    severity = {"Low": 0, "Medium": 1, "High": 2}

    def __init__(self, model: NaiveBayesHazardClassifier) -> None:
        self.rules = RuleHazardPredictor()
        self.model = LearnedHazardPredictor(model)

    def predict_label(self, text: str) -> str:
        rule_label = self.rules.predict_label(text)
        prediction = self.model.model.predict(text)
        if rule_label != "Low":
            return rule_label
        if prediction.label == "High" and prediction.confidence >= 0.9:
            return prediction.label
        return rule_label


def load_hazard_examples(path: str | Path) -> list[HazardExample]:
    dataset_path = Path(path)
    examples: list[HazardExample] = []
    for line_number, line in enumerate(
        dataset_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        payload = json.loads(line)
        label = str(payload["label"])
        if label not in LABELS:
            raise ValueError(f"invalid label on line {line_number}: {label}")
        examples.append(
            HazardExample(
                example_id=str(payload["id"]),
                text=str(payload["text"]),
                label=label,
                category=str(payload.get("category", "unspecified")),
            )
        )
    if not examples:
        raise ValueError(f"hazard dataset is empty: {dataset_path}")
    return examples


def load_ood_examples(path: str | Path) -> list[tuple[str, str]]:
    examples: list[tuple[str, str]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        examples.append((str(payload["id"]), str(payload["text"])))
    if not examples:
        raise ValueError(f"OOD dataset is empty: {path}")
    return examples


def train_hazard_classifier(
    dataset_path: str | Path,
    model_path: str | Path,
    alpha: float = 1.0,
) -> NaiveBayesHazardClassifier:
    examples = load_hazard_examples(dataset_path)
    model = NaiveBayesHazardClassifier(alpha=alpha)
    model.fit([(example.text, example.label) for example in examples])
    model.save(model_path)
    return model


def evaluate_predictor(
    predictor: HazardPredictor,
    examples: list[HazardExample],
    model_name: str,
    dataset_name: str,
) -> EvaluationReport:
    confusion = {gold: {predicted: 0 for predicted in LABELS} for gold in LABELS}
    errors: list[dict[str, str]] = []

    for example in examples:
        predicted = predictor.predict_label(example.text)
        if predicted not in LABELS:
            raise ValueError(f"predictor returned unsupported label: {predicted}")
        confusion[example.label][predicted] += 1
        if predicted != example.label:
            errors.append(
                {
                    "id": example.example_id,
                    "category": example.category,
                    "gold": example.label,
                    "predicted": predicted,
                    "text": example.text,
                }
            )

    correct = sum(confusion[label][label] for label in LABELS)
    per_class: dict[str, ClassMetrics] = {}
    for label in LABELS:
        true_positive = confusion[label][label]
        false_positive = sum(confusion[gold][label] for gold in LABELS if gold != label)
        false_negative = sum(
            confusion[label][predicted] for predicted in LABELS if predicted != label
        )
        support = sum(confusion[label].values())
        precision = _safe_divide(true_positive, true_positive + false_positive)
        recall = _safe_divide(true_positive, true_positive + false_negative)
        f1 = _safe_divide(2 * precision * recall, precision + recall)
        per_class[label] = ClassMetrics(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            support=support,
        )

    return EvaluationReport(
        model=model_name,
        dataset=dataset_name,
        examples=len(examples),
        accuracy=round(correct / len(examples), 4),
        macro_f1=round(sum(item.f1 for item in per_class.values()) / len(LABELS), 4),
        per_class=per_class,
        confusion_matrix=confusion,
        errors=tuple(errors),
        accuracy_ci95=wilson_interval(correct, len(examples)),
    )


def evaluate_safe_predictor(
    predictor: SafeHazardPredictor,
    examples: list[HazardExample],
    ood_examples: list[tuple[str, str]],
    dataset_name: str,
) -> SelectiveEvaluationReport:
    accepted = 0
    accepted_correct = 0
    high_risk_detected = 0
    high_risk_total = 0
    unsafe_false_low = 0
    errors: list[dict[str, str]] = []

    for example in examples:
        decision = predictor.assess(example.text)
        if example.label == "High":
            high_risk_total += 1
            high_risk_detected += int(decision.disposition == "accept" and decision.label == "High")
            unsafe_false_low += int(decision.disposition == "accept" and decision.label == "Low")
        if decision.disposition == "accept":
            accepted += 1
            accepted_correct += int(decision.label == example.label)
            if decision.label != example.label:
                errors.append(
                    {
                        "id": example.example_id,
                        "category": example.category,
                        "gold": example.label,
                        "predicted": str(decision.label),
                        "disposition": decision.disposition,
                        "text": example.text,
                    }
                )

    ood_rejected = sum(predictor.assess(text).disposition == "escalate" for _, text in ood_examples)
    in_domain_count = len(examples)
    return SelectiveEvaluationReport(
        dataset=dataset_name,
        in_domain_examples=in_domain_count,
        out_of_domain_examples=len(ood_examples),
        coverage=round(accepted / in_domain_count, 4),
        accepted_accuracy=round(_safe_divide(accepted_correct, accepted), 4),
        escalation_rate=round((in_domain_count - accepted) / in_domain_count, 4),
        high_risk_detection_rate=round(
            _safe_divide(high_risk_detected, high_risk_total),
            4,
        ),
        unsafe_false_low_rate=round(
            _safe_divide(unsafe_false_low, high_risk_total),
            4,
        ),
        out_of_domain_rejection_rate=round(
            _safe_divide(ood_rejected, len(ood_examples)),
            4,
        ),
        errors=tuple(errors),
        accepted_accuracy_ci95=wilson_interval(accepted_correct, accepted),
        high_risk_detection_ci95=wilson_interval(high_risk_detected, high_risk_total),
        out_of_domain_rejection_ci95=wilson_interval(ood_rejected, len(ood_examples)),
    )


def write_evaluation_report(
    reports: list[EvaluationReport],
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark": "cons-trukt-hazard-v1",
        "reports": [report.to_dict() for report in reports],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_selective_evaluation_report(
    report: SelectiveEvaluationReport,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "benchmark": "cons-trukt-hazard-selective-v2",
                "metrics": report.to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def format_selective_summary(report: SelectiveEvaluationReport) -> str:
    return "\n".join(
        [
            "| Metric | Score |",
            "| --- | ---: |",
            f"| In-domain coverage | {report.coverage:.3f} |",
            f"| Accuracy when accepted | {report.accepted_accuracy:.3f} "
            f"[{report.accepted_accuracy_ci95[0]:.2f}, {report.accepted_accuracy_ci95[1]:.2f}] |",
            f"| High-risk detection | {report.high_risk_detection_rate:.3f} "
            f"[{report.high_risk_detection_ci95[0]:.2f}, "
            f"{report.high_risk_detection_ci95[1]:.2f}] |",
            f"| Unsafe High-to-Low rate | {report.unsafe_false_low_rate:.3f} |",
            f"| OOD rejection | {report.out_of_domain_rejection_rate:.3f} |",
        ]
    )


def format_evaluation_summary(reports: list[EvaluationReport]) -> str:
    lines = [
        "| Model | Examples | Accuracy | Macro F1 | Errors |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for report in reports:
        lines.append(
            f"| {report.model} | {report.examples} | {report.accuracy:.3f} "
            f"| {report.macro_f1:.3f} | {len(report.errors)} |"
        )
    return "\n".join(lines)


def category_error_counts(
    report: EvaluationReport,
) -> dict[str, int]:
    return dict(Counter(item["category"] for item in report.errors))


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
