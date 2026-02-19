import os
import pandas as pd
import chromadb
from datetime import datetime

# --- 1. CONFIGURATION ---
DATA_FOLDER = "./training_data"
chroma_client = chromadb.PersistentClient(path="./c_os_memory")
collection = chroma_client.get_or_create_collection(name="ground_knowledge")

def ingest_csv(file_path):
    """Processes CSV datasets with high-fidelity string conversion to avoid DtypeWarnings."""
    print(f"📊 Ingesting CSV: {file_path}")
    
    # FIX: low_memory=False and dtype=str ensures all mixed data is captured correctly
    df = pd.read_csv(file_path, low_memory=False, dtype=str)
    
    # We only ingest the first 500-1000 rows of large files like 'Boiler_Permits' 
    # to keep your local ChromaDB fast while still learning the patterns.
    sample_size = min(len(df), 1000)
    df_sample = df.head(sample_size)

    for index, row in df_sample.iterrows():
        # Clean the row data to remove 'NaN' (missing values)
        clean_row = {k: v for k, v in row.items() if pd.notna(v)}
        row_str = " | ".join([f"{k}: {v}" for k, v in clean_row.items()])
        
        doc_id = f"{os.path.basename(file_path)}_line_{index}"
        collection.upsert(
            documents=[row_str],
            metadatas={"source": file_path, "type": "historical_permits"},
            ids=[doc_id]
        )
    print(f"✅ Sampled and Ingested {sample_size} records from {os.path.basename(file_path)}.")

def ingest_text_archive(file_path):
    """Processes text-based archives for geological and historical context."""
    print(f"📜 Ingesting Archive: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Split into chunks for better AI 'retrieval'
        chunks = [content[i:i+1000] for i in range(0, len(content), 800)]
        for i, chunk in enumerate(chunks):
            collection.upsert(
                documents=[chunk],
                metadatas={"source": file_path, "type": "text_archive"},
                ids=[f"{os.path.basename(file_path)}_chunk_{i}"]
            )
        print(f"✅ Ingested {len(chunks)} knowledge chunks from {os.path.basename(file_path)}.")
    except Exception as e:
        print(f"⚠️ Could not read {file_path}: {e}")

# --- 2. THE TRAINING LOOP ---
def run_full_training():
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Error: Folder {DATA_FOLDER} not found.")
        return

    files = [f for f in os.listdir(DATA_FOLDER) if os.path.isfile(os.path.join(DATA_FOLDER, f))]
    print(f"🚀 Found {len(files)} files. Starting Industrial Training...")

    for file in files:
        full_path = os.path.join(DATA_FOLDER, file)
        # Check if it's a CSV or an Archive (archive 2, 4, 66 often have no extension)
        if file.lower().endswith('.csv'):
            ingest_csv(full_path)
        else:
            ingest_text_archive(full_path)

    print("\n🌟 TRAINING SUCCESS: C-OS is now grounded in historical site data.")

if __name__ == "__main__":
    run_full_training()