# Hazard Evaluation v2

## Safety contract

The production path returns either an accepted severity assessment or
`disposition="escalate"`. It escalates empty, unfamiliar, or low-confidence
inputs instead of treating uncertainty as low risk. Deterministic life-safety,
accessibility, floodplain, stormwater, slope, and water-buffer rules take
priority over the fitted lexical classifier.

## Data

- Training: 54 examples
- Held-out in-domain test: 36 examples
- Out-of-domain rejection test: 12 examples
- Categories: slope, water, excavation cave-in protection, excavation egress,
  floodplain elevation, construction stormwater, accessible ramps, negation,
  threshold boundaries, and numeric distractors

Curated cases are based on public OSHA 1926.651/652, FEMA base-flood-elevation
guidance, EPA construction stormwater guidance, and the 2010 ADA Standards.

## Results

| Metric | Score |
| --- | ---: |
| In-domain coverage | 0.8889 |
| Accuracy on accepted cases | 1.0000 |
| In-domain escalation | 0.1111 |
| High-risk detection | 1.0000 |
| Unsafe High-to-Low rate | 0.0000 |
| Out-of-domain rejection | 1.0000 |

No accepted prediction was wrong in this fixture. Four in-domain cases were
escalated. The small curated benchmark is a regression gate, not a field
accuracy estimate or engineering certification.

## Reproduce

```bash
python scripts/build_v2_benchmarks.py
python -m cons_trukt train-hazard-model \
  --dataset benchmarks/hazard_v2/train.jsonl \
  --output artifacts/hazard_nb_v2.json
python -m cons_trukt validate-hazards
```
