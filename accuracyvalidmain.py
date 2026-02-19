import ollama, pdfplumber, json, os, pytesseract, hashlib
import cog_engine  # <--- MUST BE HERE
from pdf2image import convert_from_path
from sqlalchemy import create_engine, text
from concurrent.futures import ThreadPoolExecutor

# --- 1. CONFIGURATION ---
POPPLER_PATH = r'C:\Users\siddh\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin' 
TESSERACT_EXE = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
DB_URL = "postgresql://postgres:***REMOVED***@localhost:5432/c_os_db"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE
engine = create_engine(DB_URL, pool_size=10, max_overflow=20) 

# --- 2. GROUND CONSEQUENCE ENGINE ---
def analyze_ground_hazards(text_data):
    risk = {"level": "Low", "flags": [], "buffer": False}
    txt = text_data.upper()
    if any(x in txt for x in ["STEEP", "15%", "INCLINE", "SLOPE"]):
        risk["level"] = "High"
        risk["flags"].append("CRITICAL: Steep Slope (15%+) detected.")
    if any(x in txt for x in ["STREAM", "SURFACE WATER", "BUFFER"]):
        risk["buffer"] = True
        risk["flags"].append("ENV: Water Buffer detected.")
    return risk

# --- 3. EXTRACTION ---
def extract_text_fast(pdf_path):
    print("🚀 Extracting blueprint content...")
    content = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: content += t + "\n"
    
    if not content.strip():
        print("🔍 Scanning image layer. Starting Parallel OCR...")
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda img: pytesseract.image_to_string(img), images))
        content = "\n".join(results)
    return content

# --- 4. CORE EXECUTION ---
def run_proper_c_os(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(base_dir, filename)
    
    raw_text = extract_text_fast(pdf_path)
    hazard_report = analyze_ground_hazards(raw_text)

    print(f"🧠 Consulting Cognitive Layer (Risk: {hazard_report['level']})...")
    
    try:
        # --- CALLING THE BRAIN ---
        data = cog_engine.refine_tasks_with_history(raw_text, hazard_report)
        tasks = data.get("tasks", data)
        if isinstance(tasks, dict): tasks = [tasks]

        # Safety Overrides
        if hazard_report['level'] == "High" and not any("Slope" in t['name'] for t in tasks):
            tasks.append({"wbs": "02.50", "name": "Slope Stabilization & Erosion Control", "hours": 40})
        
        print("\n" + "="*75)
        print(f"🏗️  C-OS MASTER LEDGER: {filename.upper()} | RISK: {hazard_report['level']}")
        print("="*75)
        print(f"{'WBS':<12} | {'TASK NAME':<45} | {'HOURS':<6}")

        with engine.connect() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS smart_tasks (id SERIAL PRIMARY KEY, wbs_code VARCHAR(50), task_name TEXT, planned_hours INT, risk_level VARCHAR(20));"))
            for t in tasks:
                wbs, name, hours = str(t.get('wbs', '0.0')), str(t.get('name', 'N/A')), t.get('hours', 8)
                print(f"{wbs:<12} | {name[:43]:<45} | {hours:<6}")
                conn.execute(text("INSERT INTO smart_tasks (wbs_code, task_name, planned_hours, risk_level) VALUES (:w, :n, :h, :r)"), 
                            {"w": wbs, "n": name, "h": hours, "r": hazard_report['level']})
            conn.commit()
        print("="*75 + "\n✅ C-OS: Historical Sync Complete.\n")

    except Exception as e:
        print(f"❌ Error in main loop: {e}")

if __name__ == "__main__":
    run_proper_c_os("plan.pdf")