# Hazard Benchmark v2

This benchmark extends v1 with excavation cave-in protection, excavation
egress, floodplain elevation review, construction stormwater controls,
accessibility ramp screening, numeric distractors, boundary conditions, and a
separate out-of-domain rejection set.

The curated cases are regression fixtures derived from public requirements and
guidance. They are not jurisdiction-specific engineering determinations:

- OSHA excavation protection: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.652
- OSHA excavation access and egress: https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651
- FEMA base flood elevation: https://www.fema.gov/about/glossary/base-flood-elevation-bfe
- EPA construction stormwater: https://www.epa.gov/npdes/stormwater-discharges-construction-activities
- 2010 ADA Standards: https://www.ada.gov/law-and-regs/design-standards/2010-stds/

Rebuild the JSONL files with:

```bash
python scripts/build_v2_benchmarks.py
```
