import pandas as pd
import numpy as np
import json

# 1. Generate Geotechnical Slope Data (The Incline Factor)
def create_slope_dataset():
    data = {
        'Slope Angle': np.random.uniform(5, 45, 1000),
        'Cohesion': np.random.uniform(10, 50, 1000),
        'Factor of Safety (FS)': np.random.uniform(0.5, 2.5, 1000)
    }
    df = pd.DataFrame(data)
    # Ensure angles > 15 degrees are often marked as low Factor of Safety (Failure)
    df.loc[df['Slope Angle'] > 15, 'Factor of Safety (FS)'] -= 0.5
    df.to_csv('slope_stability_analysis.csv', index=False)
    print("✅ Created: slope_stability_analysis.csv")

# 2. Generate Industrial Task Mapping (WBS Logic)
def create_wbs_standards():
    standards = [
        {"input": "Steep Slopes (15% or more)", "task": "02.50 - Slope Stabilization", "risk": "High"},
        {"input": "Stream Buffer / Surface Water", "task": "01.50 - Silt Fencing", "risk": "High"},
        {"input": "Rockery / Rock Outcropping", "task": "02.20 - Specialized Excavation", "risk": "Medium"},
        {"input": "Underground Drain Field", "task": "01.10 - Utility Location & Protection", "risk": "High"}
    ]
    with open('industrial_standards.json', 'w') as f:
        json.dump(standards, f)
    print("✅ Created: industrial_standards.json")

if __name__ == "__main__":
    create_slope_dataset()
    create_wbs_standards()