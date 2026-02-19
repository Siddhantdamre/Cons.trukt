import ollama, pdfplumber, json, os, pytesseract, chromadb, hashlib, csv
from pdf2image import convert_from_path
from sqlalchemy import create_engine, text
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import cog_engine  # <--- MUST BE HERE

# --- 1. CONFIGURATION ---
POPPLER_PATH = r'C:\Users\siddh\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin' 
TESSERACT_EXE = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
DB_URL = "postgresql://postgres:***REMOVED***@localhost:5432/c_os_db"
MODEL_NAME = 'llama3.2'

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
engine = create_engine(DB_URL, pool_size=10, max_overflow=20) 
chroma_client = chromadb.PersistentClient(path="./c_os_memory")
collection = chroma_client.get_or_create_collection(name="ground_knowledge")

# --- 2. GROUND CONSEQUENCE ENGINE ---
def analyze_ground_hazards(text_data):
    risk = {"level": "Low", "flags": [], "buffer": False}
    txt = text_data.upper()
    
    # BROADENED DETECTION: Looking for '15%' or 'STEEP' anywhere in the 7 pages
    if any(x in txt for x in ["STEEP", "15%", "INCLINE", "SLOPE"]):
        risk["level"] = "High"
        risk["flags"].append("CRITICAL: Steep Slope (15%+) detected.")
    
    if any(x in txt for x in ["STREAM", "SURFACE WATER", "BUFFER", "WETLAND"]):
        risk["buffer"] = True
        risk["flags"].append("ENV: Water/Stream Buffer detected.")
        if risk["level"] == "Low": risk["level"] = "Medium"
        
    return risk

# --- 3. EXTRACTION ---
def ocr_page(img):
    return pytesseract.image_to_string(img)

def extract_text_fast(pdf_path):
    print("🚀 Extracting blueprint content...")
    content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: content += t + "\n"
    
    if not content.strip():
        print("🔍 Digital layer empty. Starting Parallel OCR...")
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(ocr_page, images))
        content = "\n".join(results)
    return content

# --- 4. CORE EXECUTION ---
def run_proper_c_os(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, filename)
    
    raw_text = extract_text_fast(pdf_path)
    hazard_report = analyze_ground_hazards(raw_text)

    # FIX: We escape curly braces by replacing '{' with '{{' and '}' with '}}'
    # This prevents the "Invalid format specifier" error
    escaped_text = raw_text[:8000].replace("{", "{{").replace("}", "}}")

    print(f"🧠 Reasoning (Risk: {hazard_report['level']})...")
    
    # We use double braces for the JSON structure in the f-string
    prompt = f"""
    Risk Flags: {hazard_report['flags']}
    Blueprints: {escaped_text}
    
    Task: Extract construction actions as a JSON list.
    FORMAT: {{"tasks": [{{"wbs": "code", "name": "task", "hours": 0}}]}}
    """
    
    try:
        data = cog_engine.refine_tasks_with_history(raw_text, hazard_report)
        data = json.loads(response['message']['content'])
        
        # Extract the list of tasks
        tasks = data.get("tasks", data)
        if isinstance(tasks, dict): tasks = [tasks]

        print("\n" + "="*60)
        print(f"🏗️  C-OS MASTER LEDGER: {filename.upper()}")
        print(f"🚩 RISK: {hazard_report['level']} | BUFFER: {hazard_report['buffer']}")
        print("="*60)
        print(f"{'WBS':<10} | {'TASK NAME':<35} | {'HOURS':<6}")

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS smart_tasks (id SERIAL PRIMARY KEY, wbs_code VARCHAR(50), task_name TEXT, planned_hours INT, risk_level VARCHAR(20));"))
            
            for t in tasks:
                wbs = str(t.get('wbs', '0.0'))
                name = str(t.get('name', 'N/A'))
                hours = t.get('hours', 0)
                
                print(f"{wbs:<10} | {name[:33]:<35} | {hours:<6}")
                conn.execute(text("INSERT INTO smart_tasks (wbs_code, task_name, planned_hours, risk_level) VALUES (:w, :n, :h, :r)"), 
                            {"w": wbs, "n": name, "h": hours, "r": hazard_report['level']})
            conn.commit()
        print("="*60 + "\n✅ C-OS: Sync Complete.\n")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_proper_c_os("plan.pdf")