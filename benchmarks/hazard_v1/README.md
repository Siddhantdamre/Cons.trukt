# Cons.trukt Hazard Benchmark v1

This benchmark evaluates three-way construction-site hazard classification:

- `Low`: no material topographical or water constraint in the supplied text
- `Medium`: water, wetland, stream-buffer, or drainage constraint without steep-slope risk
- `High`: steep grade, instability, landslide, or explicit slope-stabilization requirement

The dataset contains 36 training examples and 18 held-out test examples. It is
synthetic and deliberately compact, so it measures regression behavior rather
than real-world engineering validity. Test cases include negation, benign
topographic language, numeric grade thresholds, water-only constraints, and
combined hazards.

Run:

```bash
python -m cons_trukt train-hazard-model
python -m cons_trukt evaluate-hazards
```

The evaluation reports accuracy, macro F1, per-class precision/recall/F1,
confusion matrices, and every misclassified example.
