# Hazard selective evaluation - hard out-of-distribution slice (v3)

The v2 selective evaluation reported 100% out-of-distribution (OOD) rejection,
but its OOD set was clearly off-domain (carpet colors, sports scores). This v3
slice adds 12 near-domain adversarial prompts: construction-flavored but not
hazard-severity questions involving bids, schedules, RFIs, signage, and
translation. Every proportion includes a 95% Wilson confidence interval because
the benchmark remains small.

Command:

```bash
python -m cons_trukt validate-hazards \
  --dataset benchmarks/hazard_v2/test.jsonl \
  --ood-dataset benchmarks/hazard_v2/ood_v3.jsonl \
  --model artifacts/hazard_nb_v2.json \
  --output results/hazard_v2/selective_evaluation_v3.json
```

Result (36 in-domain, 24 OOD):

| Metric | Score | 95% CI |
| --- | ---: | ---: |
| In-domain coverage | 0.889 | - |
| Accuracy when accepted | 1.000 | [0.89, 1.00] |
| High-risk detection | 1.000 | [0.76, 1.00] |
| Unsafe High-to-Low rate | 0.000 | - |
| **OOD rejection** | **1.000** | **[0.86, 1.00]** |

## Closed failure

The original vocabulary-only boundary accepted `adv-ood-11`, "Translate the
parking instructions into Spanish for the crew," as `Medium`. Site terms such
as "parking" and "crew" obscured the fact that the input requested translation,
not hazard assessment.

`HazardIntentGate` now runs before deterministic rules and the fitted
classifier. It recognizes direct translation, summarization, document-drafting,
scheduling, reservation, recommendation, and forecasting commands. The
formerly leaked prompt now returns:

- `disposition="escalate"`
- `detected_intent="translation"`
- an explicit reason stating that the request is not a hazard assessment

In-domain coverage, accepted accuracy, high-risk detection, and the unsafe
High-to-Low rate are unchanged.

## Limits

The intent gate recognizes explicit workflow-command forms; it is not universal
intent understanding. Indirect or novel non-hazard requests can still reach the
vocabulary and confidence gates. Even at 1.0, high-risk detection's CI is
[0.76, 1.00], so this compact benchmark cannot establish field accuracy.
