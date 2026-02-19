import chromadb
import pandas as pd
import json
import hashlib

# Initialize Memory
chroma_client = chromadb.PersistentClient(path="./c_os_memory")
collection = chroma_client.get_or_create_collection(name="ground_knowledge")

def train_from_geotechnical_data():
    df = pd.read_csv('slope_stability_analysis.csv')
    high_risk = df[df['Factor of Safety (FS)'] < 1.0] # Identify failure cases
    
    print(f"📉 Ingesting {len(high_risk)} high-risk incline studies...")
    for idx, row in high_risk.iterrows():
        content = f"Incline: {row['Slope Angle']:.2f}° | Hazard: Structural Failure | Action: Reinforcement"
        collection.upsert(
            documents=[content],
            metadatas={"type": "geotechnical", "risk": "High"},
            ids=[f"slope_{idx}"]
        )

def train_from_wbs_standards():
    with open('industrial_standards.json', 'r') as f:
        standards = json.load(f)
    
    print(f"📘 Ingesting {len(standards)} industrial WBS standards...")
    for idx, std in enumerate(standards):
        content = f"Condition: {std['input']} | Required Task: {std['task']} | Level: {std['risk']}"
        collection.upsert(
            documents=[content],
            metadatas={"type": "standards"},
            ids=[f"std_{idx}"]
        )

if __name__ == "__main__":
    train_from_geotechnical_data()
    train_from_wbs_standards()
    print("\n🚀 C-OS TRAINING COMPLETE. Memory is now Ground-Aware.")