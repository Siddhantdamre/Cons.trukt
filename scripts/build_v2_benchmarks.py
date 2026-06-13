"""Build the harder hazard-v2 benchmark from v1 plus curated edge cases."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "benchmarks" / "hazard_v1"
V2 = ROOT / "benchmarks" / "hazard_v2"

OSHA_EXCAVATION = "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.652"
OSHA_EGRESS = "https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.651"
FEMA_BFE = "https://www.fema.gov/about/glossary/base-flood-elevation-bfe"
EPA_STORMWATER = "https://www.epa.gov/npdes/stormwater-discharges-construction-activities"
ADA_STANDARDS = "https://www.ada.gov/law-and-regs/design-standards/2010-stds/"


def case(
    case_id: str,
    text: str,
    label: str,
    category: str,
    source_url: str,
) -> dict[str, Any]:
    return {
        "id": case_id,
        "text": text,
        "label": label,
        "category": category,
        "source_url": source_url,
    }


TRAIN_CASES = [
    case(
        "v2-train-low-01",
        "A three-foot trench in stable rock has a secured ladder.",
        "Low",
        "excavation-safe",
        OSHA_EGRESS,
    ),
    case(
        "v2-train-low-02",
        "The four-foot excavation uses a trench box and documented safe egress.",
        "Low",
        "excavation-safe",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-train-low-03",
        "The accessible ramp is 1:12 and includes level landings.",
        "Low",
        "accessibility-compliant",
        ADA_STANDARDS,
    ),
    case(
        "v2-train-low-04",
        "The parcel is outside the mapped floodplain and no BFE review applies.",
        "Low",
        "floodplain-negation",
        FEMA_BFE,
    ),
    case(
        "v2-train-low-05",
        "Interior finish work disturbs no soil and creates no stormwater discharge.",
        "Low",
        "stormwater-negation",
        EPA_STORMWATER,
    ),
    case(
        "v2-train-low-06",
        "The lobby flooring contains eighteen percent recycled aggregate.",
        "Low",
        "percentage-distractor",
        ADA_STANDARDS,
    ),
    case(
        "v2-train-medium-01",
        "The proposed structure lies in a mapped floodplain and requires BFE documentation.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-train-medium-02",
        "Base flood elevation and finished-floor elevation must be verified.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-train-medium-03",
        "Construction stormwater discharge requires erosion and sediment controls.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-train-medium-04",
        "Disturbed soil will need stabilization and runoff inspections after storms.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-train-medium-05",
        "A flood hazard area overlaps the parking expansion.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-train-medium-06",
        "The site plan calls for sediment control before mass grading.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-train-high-01",
        "An eight-foot trench in unstable soil lacks a protective system.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-train-high-02",
        "The six-foot excavation has no shoring, sloping, benching, or trench box.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-train-high-03",
        "A five-foot trench has no ladder, ramp, stairway, or safe egress.",
        "High",
        "excavation-egress",
        OSHA_EGRESS,
    ),
    case(
        "v2-train-high-04",
        "The accessible entrance ramp is 1:10 and therefore too steep.",
        "High",
        "accessibility-ramp",
        ADA_STANDARDS,
    ),
    case(
        "v2-train-high-05",
        "A 1:11 ramp lacks a level landing at the doorway.",
        "High",
        "accessibility-ramp",
        ADA_STANDARDS,
    ),
    case(
        "v2-train-high-06",
        "Workers entered a seven-foot trench with cave-in risk and no trench box.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
]

TEST_CASES = [
    case(
        "v2-test-low-01",
        "Concrete mix design specifies 21 percent fly ash on a level site.",
        "Low",
        "percentage-distractor",
        EPA_STORMWATER,
    ),
    case(
        "v2-test-low-02",
        "A compliant 1:12 route has landings and handrails at the public entrance.",
        "Low",
        "accessibility-compliant",
        ADA_STANDARDS,
    ),
    case(
        "v2-test-low-03",
        "The project is outside the flood hazard area and above the mapped BFE.",
        "Low",
        "floodplain-negation",
        FEMA_BFE,
    ),
    case(
        "v2-test-low-04",
        "A shallow three-foot utility trench has stable sides and a ladder.",
        "Low",
        "excavation-safe",
        OSHA_EGRESS,
    ),
    case(
        "v2-test-low-05",
        "No soil disturbance or construction stormwater discharge is proposed.",
        "Low",
        "stormwater-negation",
        EPA_STORMWATER,
    ),
    case(
        "v2-test-low-06",
        "Existing grade is 14.9 percent with no instability or drainage issue.",
        "Low",
        "threshold-boundary",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-test-medium-01",
        "Floodplain development requires base flood elevation documentation.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-test-medium-02",
        "The addition is inside a special flood hazard area.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-test-medium-03",
        "Mass grading will discharge construction stormwater from disturbed soil.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-test-medium-04",
        "The erosion-control plan requires sediment barriers and stabilization.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-test-medium-05",
        "Finished floor elevation must be compared with the BFE.",
        "Medium",
        "floodplain",
        FEMA_BFE,
    ),
    case(
        "v2-test-medium-06",
        "Runoff inspections are required while the construction site remains exposed.",
        "Medium",
        "stormwater",
        EPA_STORMWATER,
    ),
    case(
        "v2-test-high-01",
        "Trench is 8 feet deep in unstable soil and lacks protective system.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-test-high-02",
        "A six-foot excavation is open with no trench box or shoring.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
    case(
        "v2-test-high-03",
        "The five-foot trench has no ladder or other safe egress.",
        "High",
        "excavation-egress",
        OSHA_EGRESS,
    ),
    case(
        "v2-test-high-04",
        "Accessible ramp slope is 1:10 with no landing.",
        "High",
        "accessibility-ramp",
        ADA_STANDARDS,
    ),
    case(
        "v2-test-high-05",
        "The entry route uses a 1:9 ramp without a level landing.",
        "High",
        "accessibility-ramp",
        ADA_STANDARDS,
    ),
    case(
        "v2-test-high-06",
        "A seven-foot trench in collapsing soil has no protective system.",
        "High",
        "excavation-protection",
        OSHA_EXCAVATION,
    ),
]

OOD_CASES = [
    {"id": "ood-01", "text": "What color should the lobby carpet be?"},
    {"id": "ood-02", "text": "Predict next quarter's mortgage interest rate."},
    {"id": "ood-03", "text": "Write a birthday poem for the project manager."},
    {"id": "ood-04", "text": "Which laptop should the accounting team purchase?"},
    {"id": "ood-05", "text": "Summarize the football match from last night."},
    {"id": "ood-06", "text": "How many calories are in this lunch order?"},
    {"id": "ood-07", "text": "Translate this wedding invitation into French."},
    {"id": "ood-08", "text": "Recommend a science-fiction movie for Friday."},
    {"id": "ood-09", "text": "Should we change the company logo font?"},
    {"id": "ood-10", "text": "Estimate the resale value of a used phone."},
    {"id": "ood-11", "text": "Draft a social media caption for a coffee shop."},
    {"id": "ood-12", "text": "Who will win the election?"},
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )


def main() -> None:
    write_jsonl(V2 / "train.jsonl", read_jsonl(V1 / "train.jsonl") + TRAIN_CASES)
    write_jsonl(V2 / "test.jsonl", read_jsonl(V1 / "test.jsonl") + TEST_CASES)
    write_jsonl(V2 / "ood.jsonl", OOD_CASES)


if __name__ == "__main__":
    main()
