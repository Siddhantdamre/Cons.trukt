import chromadb, ollama, json

MODEL_NAME = 'llama3.2'

def refine_tasks_with_history(blueprint_text, hazard_report):
    # Connect to the memory you populated with the 6,000+ permit records
    chroma_client = chromadb.PersistentClient(path="./c_os_memory")
    collection = chroma_client.get_or_create_collection(name="ground_knowledge")

    # 1. Search for historical precedents
    query_text = f"risks and permit tasks for {hazard_report['level']} projects with {hazard_report['flags']}"
    results = collection.query(query_texts=[query_text], n_results=5)
    history = "\n".join(results['documents'][0])
    
    # 2. Escape text for prompt
    escaped_blueprint = blueprint_text[:12000].replace("{", "{{").replace("}", "}}")
    
    prompt = f"""
    SYSTEM: You are the C-OS Industrial Engine.
    
    1. PRIMARY DATA (The "Visual Truth" - DO NOT IGNORE):
    {escaped_blueprint}

    2. SECONDARY CONTEXT (Historical Permit Patterns):
    {history}

    TASK:
    Extract ONLY the tasks physically described in the PRIMARY DATA (Garage, Deck, Concrete). 
    Use the SECONDARY CONTEXT only to adjust the HOURS and PROFESSIONAL NAMES of those tasks.
    
    CRITICAL: Do not hallucinate roofing or chimneys if they are not in the primary data.
    
    FORMAT: {{"tasks": [{{"wbs": "CSI_Code", "name": "Task Name", "hours": float}}]}}
    """
    
    response = ollama.chat(model=MODEL_NAME, format='json', messages=[{'role': 'user', 'content': prompt}])
    return json.loads(response['message']['content'])