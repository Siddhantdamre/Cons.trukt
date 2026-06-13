# Hazard Benchmark v1

## Objective

Measure whether Cons.trukt can classify short construction-plan excerpts into:

- `Low`: no material slope or water constraint
- `Medium`: water, wetland, stream-buffer, or drainage constraint
- `High`: steep grade, instability, landslide, or stabilization requirement

## Dataset

The benchmark is synthetic and versioned under `benchmarks/hazard_v1/`.

| Split | Examples | Low | Medium | High |
| --- | ---: | ---: | ---: | ---: |
| Train | 36 | 12 | 12 | 12 |
| Held out | 18 | 6 | 6 | 6 |

The held-out split includes numeric thresholds, written-out percentages,
negated hazards, benign topographic references, off-site notes, water-only
constraints, and combined slope/water cases.

## Systems

1. `rule`: deterministic `HazardAnalyzer`
2. `naive_bayes`: dependency-free multinomial Naive Bayes trained on the 36 examples
3. `hybrid`: rules with a conservative learned-model fallback

## Reproduction

```bash
python -m cons_trukt train-hazard-model \
  --dataset benchmarks/hazard_v1/train.jsonl \
  --output artifacts/hazard_nb_v1.json

python -m cons_trukt evaluate-hazards \
  --dataset benchmarks/hazard_v1/test.jsonl \
  --model artifacts/hazard_nb_v1.json \
  --output results/hazard_v1/evaluation.json
```

## Results

| System | Accuracy | Macro F1 | Errors |
| --- | ---: | ---: | ---: |
| Rule | 1.000 | 1.000 | 0 |
| Naive Bayes | 0.778 | 0.763 | 4 |
| Hybrid | 1.000 | 1.000 | 0 |

The learned baseline correctly classified all six medium-risk cases, but missed
two low-risk negation/benign-context cases and two high-risk cases. The
deterministic analyzer performed best after adding explicit handling for:

- percent signs and the word `percent`
- slope context around numeric values
- scoped negation and off-site notes
- surface-runoff language
- retaining-wall and instability phrasing

## Interpretation

This result demonstrates reproducible regression coverage and an auditable
baseline comparison. It does not establish real-world engineering validity.
The next benchmark version should use expert-reviewed, de-identified plan
excerpts and report inter-annotator agreement.
