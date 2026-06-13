"""Synthetic seed data generation for local experiments."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path


def generate_seed_data(output_dir: str | Path, rows: int = 1000) -> tuple[Path, Path]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    slope_path = root / "slope_stability_analysis.csv"
    standards_path = root / "industrial_standards.json"

    random.seed(42)
    with slope_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["Slope Angle", "Cohesion", "Factor of Safety (FS)"],
        )
        writer.writeheader()
        for _ in range(rows):
            slope_angle = random.uniform(5, 45)
            cohesion = random.uniform(10, 50)
            factor_of_safety = random.uniform(0.5, 2.5)
            if slope_angle > 15:
                factor_of_safety -= 0.5
            writer.writerow(
                {
                    "Slope Angle": f"{slope_angle:.2f}",
                    "Cohesion": f"{cohesion:.2f}",
                    "Factor of Safety (FS)": f"{factor_of_safety:.2f}",
                }
            )

    standards = [
        {"input": "Steep Slopes (15% or more)", "task": "02.50 - Slope Stabilization", "risk": "High"},
        {"input": "Stream Buffer / Surface Water", "task": "01.50 - Silt Fencing", "risk": "High"},
        {"input": "Rockery / Rock Outcropping", "task": "02.20 - Specialized Excavation", "risk": "Medium"},
        {"input": "Underground Drain Field", "task": "01.10 - Utility Location & Protection", "risk": "High"},
    ]
    standards_path.write_text(json.dumps(standards, indent=2), encoding="utf-8")
    return slope_path, standards_path
