# Demo Upgrade Roadmap

Goal: convert Cons.trukt into a concrete construction document intelligence demo with safe sample files and visible risk output.

## Current State

- GitHub Pages surface is live.
- README explains the construction intelligence concept, API shape, and roadmap.
- The repo has a strong domain-specific story, but needs fixture data and screenshots.

## Highest-Impact Improvements

| Priority | Upgrade | Recruiter value |
| --- | --- | --- |
| P0 | Add `examples/` with synthetic borehole, blueprint, and site-log inputs. | Makes the project reproducible without private data. |
| P0 | Add a Streamlit demo that runs on sample files. | Makes the product workflow clickable. |
| P1 | Add dashboard screenshots for risk, carbon, and ledger output. | Makes the output tangible. |
| P1 | Add Docker or Docker Compose for one-command local review. | Signals deployability. |
| P2 | Add a disclaimer and validation notes for engineering decision support. | Shows responsible product framing. |

## Suggested Demo Shape

- Streamlit file picker with bundled sample files.
- Output tabs: parsed data, risk findings, recommendation, ledger hash, carbon estimate.
- Optional FastAPI `/docs` screenshot for backend credibility.

## Definition Of Done

- Reviewer can run or open a demo and inspect one complete construction analysis flow.
- No private or real construction data is required.
- README includes screenshots and sample JSON output.
