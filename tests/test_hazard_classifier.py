from __future__ import annotations

from cons_trukt.evaluation import (
    HazardExample,
    LearnedHazardPredictor,
    evaluate_predictor,
)
from cons_trukt.models.hazard_classifier import NaiveBayesHazardClassifier, tokenize


def test_tokenize_keeps_percent_signal_and_bigrams():
    tokens = tokenize("A steep 18% slope")

    assert "18_percent" in tokens
    assert "steep__18_percent" in tokens


def test_classifier_round_trip(tmp_path):
    model = NaiveBayesHazardClassifier().fit(
        [
            ("flat dry site", "Low"),
            ("wetland buffer", "Medium"),
            ("steep 20% slope", "High"),
        ]
    )
    path = model.save(tmp_path / "model.json")
    restored = NaiveBayesHazardClassifier.load(path)

    assert restored.predict("steep slope").label == "High"


def test_evaluation_reports_confusion_and_macro_f1():
    model = NaiveBayesHazardClassifier().fit(
        [
            ("flat ground", "Low"),
            ("stream buffer", "Medium"),
            ("steep slope", "High"),
        ]
    )
    examples = [
        HazardExample("1", "flat ground", "Low", "flat"),
        HazardExample("2", "stream buffer", "Medium", "water"),
        HazardExample("3", "steep slope", "High", "slope"),
    ]

    report = evaluate_predictor(
        LearnedHazardPredictor(model),
        examples,
        model_name="test",
        dataset_name="unit",
    )

    assert report.accuracy == 1.0
    assert report.macro_f1 == 1.0
    assert report.errors == ()
