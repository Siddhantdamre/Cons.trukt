# 🏗️ C-OS Nexus (Construction Operating System)

[![Version](https://img.shields.io/badge/Version-v60.0_Prometheus-blue.svg)]()
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)]()
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)]()
[![AI](https://img.shields.io/badge/Agentic_AI-Llama_3.2-purple.svg)]()

**C-OS Nexus** is an autonomous, real-time cyber-physical operating system for the construction industry. It bridges the "Automation Gap" by actively ingesting raw site data (drone scans, borehole logs), applying rigorous geotechnical physics, and outputting liability-backed engineering decisions in milliseconds.

C-OS eliminates the multi-week latency between site discovery and engineering action, autonomously optimizing for **Risk, Schedule, Cash Flow, and Carbon Equity (SDG-12)**.

---

## 🚀 The Core Problem Solved
Traditional construction projects bleed capital due to data silos. By the time a geotechnical engineer analyzes a soil report in an Excel sheet, the pile driver is already on site. 
**C-OS functions as a Real-Time Decision Support System**, acting as the connective intelligence layer between physical site sensors and project management software (like Procore or Autodesk Build).

## ✨ Enterprise Features

### 1. 🔬 Validated Geotechnical Physics Engine
* **Terzaghi Bearing Capacity:** Evaluates shallow and deep foundation viability instantly.
* **Rock Mechanics Override:** Detects global geological profiles (e.g., South Korean "Yeon-am" soft rock vs. "Gyeong-am" hard bedrock) and adjusts calculations to Rock Mass Rating heuristics ($N \ge 50 \rightarrow 5000 \text{ kPa}$).
* **Seismic Liquefaction Detection:** Autonomously flags high-risk profiles (e.g., loose sands with a high water table) and prescribes remediation (e.g., Deep Vibro-Compaction).

### 2. 👁️ Autonomous Reality Capture (ARC)
* Processes noisy, real-world PDF blueprints and site scans at 300 DPI.
* Utilizes Canny edge gradients and computer vision to calculate terrain density indices, automatically flagging highly complex topography for structural review.

### 3. 🌱 Carbon Equity & SDG-12 Compliance
* Transforms site waste into bankable environmental assets.
* Calculates precise CO2-e mitigation ($0.54\text{ tons } CO_2\text{-e/ton}$ diverted) based on a target 82% circular economy waste recovery rate.

### 4. 🔐 The "Golden Record" (Immutable Ledger)
* Every AI and physics-based decision is cryptographically signed using **SHA-512 hashing**.
* Creates an unalterable audit trail for liability protection, dispute resolution, and insurance compliance.

### 5. 🤖 Multi-Agent Swarm (Llama 3.2 RAG)
* **Engineer Agent:** Cross-references 5,900+ historical precedents to ensure code compliance.
* **ESG Auditor:** Tracks sustainability metrics.
* **Logistics Agent:** Projects supply chain volatility and lead times.
* Outputs natively in **CSI MasterFormat** codes for instant ERP integration.

---

## 📐 System Architecture :

C-OS is built as a highly scalable, event-driven API Microservice.

1. **Polymorphic Ingestor:** Accepts `.csv` (Sensor logs/Boreholes), `.pdf` (Drone/ARC scans), or `.json` (BIM models).
2. **Nexus Core (FastAPI):** Asynchronous processing engine handling physics math and agentic negotiation.
3. **Frontend Dashboard:** A Streamlit-based executive view for real-time risk assessment.

---

## ⚙️ Installation & Deployment :

### Option A: Docker Deployment (Recommended for Production)
The quickest way to deploy the API with all required system binaries (Tesseract, Poppler).

```bash
# 1. Clone the repository
git clone [https://github.com/YOUR_USERNAME/c-os-nexus.git](https://github.com/YOUR_USERNAME/c-os-nexus.git)
cd c-os-nexus

# 2. Build the Docker container
docker build -t c-os-nexus .

# 3. Run the server
docker run -p 8000:8000 c-os-nexus

Option B: Local Python Setup
Ensure you have poppler-utils and tesseract-ocr installed on your host machine.

# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the Ollama Neural Engine (Requires Ollama installed locally)
ollama serve &
ollama pull llama3.2

📡 API Usage
Endpoint: /api/v1/ingest
Upload any site data file. The polymorphic router will identify the data type, apply the correct physics/vision models, and return a standardized JSON payload.

cURL Example:

Bash - 
curl -X 'POST' \
  'http://localhost:8000/api/v1/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@site_borehole_log.csv'
JSON Response Example:

JSON - 
{
    "status": "SUCCESS",
    "processing_time": "0.0412s",
    "ledger_hash": "38cb3aeb3d91069bff1563f1033151c2caedbe4dea...",
    "payload": {
        "type": "GEOTECH_ANALYSIS",
        "recommendation": "DEEP_VIBRO_COMPACTION",
        "layers": [
            {
                "depth": 3.0,
                "capacity": 73.0,
                "decision": "REJECTED (Settlement Risk)"
            },
            {
                "depth": 6.0,
                "capacity": 0.0,
                "decision": "CRITICAL: LIQUEFACTION RISK"
            },
            {
                "depth": 18.0,
                "capacity": 5000.0,
                "decision": "APPROVED (Bedrock Socket)"
            }
        ]
    }
}
👨‍💻 Executive Dashboard (Zero-UI) -
To launch the client-facing visual interface (assuming you have deployed the Streamlit module):

Bash - 
"streamlit run dashboard.py"
This renders the Executive God-Mode view, translating the raw JSON API output into interactive geotechnical profiles, carbon tracking, and financial impact summaries.

📄 License & Disclaimer
 - MIT License.

Disclaimer: C-OS Nexus is a decision-support system. While built on rigorous physics (e.g., Terzaghi's bearing capacity equations), all outputs should be reviewed by a licensed Professional Engineer (PE) before physical construction begins.

# 3. Boot the FastAPI Server
uvicorn main:app --host 0.0.0.0 --port 8000