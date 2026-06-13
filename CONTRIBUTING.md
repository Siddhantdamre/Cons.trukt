# Contributing to Cons.trukt

Cons.trukt is a safety-oriented decision-support prototype. Contributions must
favor explicit uncertainty and human escalation over unsupported automation.

## Development setup

```bash
python -m pip install -e ".[dev]"
make verify
```

On Windows without `make`, run:

```powershell
python -m ruff check src scripts tests
python -m mypy src
python -m pytest -q
```

## Evaluation

Run `make evaluate` after changing hazard rules, intent screening, the fitted
classifier, retrieval, benchmark fixtures, or acceptance thresholds.

Hazard changes must report:

- in-domain coverage and accuracy when accepted;
- high-risk detection and unsafe High-to-Low rate;
- out-of-domain rejection on `benchmarks/hazard_v2/ood_v3.jsonl`;
- sample counts and 95% confidence intervals.

## Pull requests

- Add a regression test for every fixed failure mode.
- Keep network, OCR, database, and model integrations lazy at import time.
- Never convert an uncertain condition to `Low`; escalate it.
- Cite authoritative public guidance for new regulatory benchmark records.
- Do not commit credentials, private project records, generated caches, model
  weights, or database exports.
- State clearly when a result is synthetic regression evidence rather than
  field validation or engineering certification.

By contributing, you agree that your contribution is licensed under the MIT
License.
