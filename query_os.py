import chromadb

chroma_client = chromadb.PersistentClient(path="./c_os_memory")
collection = chroma_client.get_or_create_collection(name="ground_knowledge")

def ask_c_os(question):
    print(f"🔍 Searching C-OS Memory for: '{question}'...")
    results = collection.query(query_texts=[question], n_results=3)
    
    print("\n" + "="*50)
    print("🧠 HISTORICAL GROUND TRUTH")
    print("="*50)
    for i, doc in enumerate(results['documents'][0]):
        source = results['metadatas'][0][i]['source']
        print(f"[{i+1}] Source: {source}\n    {doc[:200]}...\n")
    print("="*50)

if __name__ == "__main__":
    # Test it with a topic from your training data
    ask_c_os("common reasons for plan review rejection on steep slopes")