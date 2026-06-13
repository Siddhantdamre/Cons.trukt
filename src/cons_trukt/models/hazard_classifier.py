"""Small, dependency-free text classifier for construction hazard severity."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

LABELS = ("Low", "Medium", "High")


def tokenize(text: str) -> list[str]:
    """Tokenize text into normalized unigrams and adjacent bigrams."""
    normalized = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"\1_percent", text.lower())
    normalized = re.sub(r"(\d+(?:\.\d+)?)\s+percent", r"\1_percent", normalized)
    words = re.findall(r"[a-z0-9_]+", normalized)
    bigrams = [f"{left}__{right}" for left, right in zip(words, words[1:], strict=False)]
    features = words + bigrams

    hazard_terms = (
        "slope",
        "grade",
        "incline",
        "wetland",
        "stream",
        "buffer",
        "drainage",
    )
    if re.search(
        rf"\b(?:no|not|without|absent)\b.{{0,40}}\b(?:{'|'.join(hazard_terms)})\b",
        normalized,
    ):
        features.append("feature_negated_hazard")
    if any(
        term in normalized
        for term in ("wetland", "stream", "surface runoff", "surface water", "drainage")
    ):
        features.append("feature_water_constraint")
    if any(
        term in normalized
        for term in ("landslide", "unstable", "steep", "stabilization", "eroding")
    ):
        features.append("feature_slope_instability")

    for match in re.finditer(r"\b(\d+(?:\.\d+)?)_percent\b", normalized):
        window = normalized[max(0, match.start() - 30) : match.end() + 30]
        if any(term in window for term in ("slope", "grade", "incline", "contour")):
            value = float(match.group(1))
            features.append("feature_grade_ge_15" if value >= 15 else "feature_grade_lt_15")

    return features


@dataclass(frozen=True)
class HazardPrediction:
    label: str
    confidence: float
    probabilities: dict[str, float]
    known_token_ratio: float


class NaiveBayesHazardClassifier:
    """Multinomial Naive Bayes baseline with serializable model state."""

    def __init__(self, alpha: float = 1.0) -> None:
        if alpha <= 0:
            raise ValueError("alpha must be positive")
        self.alpha = alpha
        self.class_counts: Counter[str] = Counter()
        self.token_counts: dict[str, Counter[str]] = defaultdict(Counter)
        self.total_tokens: Counter[str] = Counter()
        self.vocabulary: set[str] = set()

    def fit(self, examples: list[tuple[str, str]]) -> NaiveBayesHazardClassifier:
        if not examples:
            raise ValueError("at least one training example is required")
        self.class_counts.clear()
        self.token_counts.clear()
        self.total_tokens.clear()
        self.vocabulary.clear()

        for text, label in examples:
            if label not in LABELS:
                raise ValueError(f"unsupported hazard label: {label}")
            tokens = tokenize(text)
            self.class_counts[label] += 1
            self.token_counts[label].update(tokens)
            self.total_tokens[label] += len(tokens)
            self.vocabulary.update(tokens)
        return self

    def predict(self, text: str) -> HazardPrediction:
        if not self.class_counts:
            raise RuntimeError("classifier must be fitted before prediction")

        tokens = tokenize(text)
        total_examples = sum(self.class_counts.values())
        vocabulary_size = max(1, len(self.vocabulary))
        log_scores: dict[str, float] = {}

        for label in LABELS:
            class_count = self.class_counts[label]
            prior = (class_count + self.alpha) / (total_examples + self.alpha * len(LABELS))
            denominator = self.total_tokens[label] + self.alpha * vocabulary_size
            score = math.log(prior)
            for token in tokens:
                numerator = self.token_counts[label][token] + self.alpha
                score += math.log(numerator / denominator)
            log_scores[label] = score

        probabilities = _softmax(log_scores)
        label = max(probabilities, key=lambda candidate: probabilities[candidate])
        return HazardPrediction(
            label=label,
            confidence=round(probabilities[label], 6),
            probabilities={key: round(value, 6) for key, value in probabilities.items()},
            known_token_ratio=self.known_token_ratio(text),
        )

    def known_token_ratio(self, text: str) -> float:
        """Return unigram vocabulary coverage as a simple OOD signal."""
        unigrams = {
            token
            for token in tokenize(text)
            if "__" not in token and not token.startswith("feature_")
        }
        if not unigrams:
            return 0.0
        known = sum(token in self.vocabulary for token in unigrams)
        return round(known / len(unigrams), 6)

    def save(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_type": "multinomial_naive_bayes",
            "version": 1,
            "alpha": self.alpha,
            "labels": list(LABELS),
            "class_counts": dict(self.class_counts),
            "token_counts": {label: dict(self.token_counts[label]) for label in LABELS},
            "total_tokens": dict(self.total_tokens),
            "vocabulary": sorted(self.vocabulary),
        }
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return output_path

    @classmethod
    def load(cls, path: str | Path) -> NaiveBayesHazardClassifier:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("model_type") != "multinomial_naive_bayes":
            raise ValueError("unsupported hazard model artifact")

        model = cls(alpha=float(payload["alpha"]))
        model.class_counts.update(payload["class_counts"])
        for label, counts in payload["token_counts"].items():
            model.token_counts[label].update(counts)
        model.total_tokens.update(payload["total_tokens"])
        model.vocabulary.update(payload["vocabulary"])
        return model


def _softmax(log_scores: dict[str, float]) -> dict[str, float]:
    maximum = max(log_scores.values())
    exponentials = {label: math.exp(score - maximum) for label, score in log_scores.items()}
    total = sum(exponentials.values())
    return {label: value / total for label, value in exponentials.items()}
