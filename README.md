# Cons.trukt / C-OS

Cons.trukt is an experimental Python-based construction intelligence prototype. It combines PDF blueprint extraction, OCR, rule-based hazard detection, local retrieval over permit history, LLM task generation, and PostgreSQL persistence to turn unstructured construction documents into a task ledger.

This repository is best understood as a working prototype rather than a production-ready application. The code proves the workflow end to end, but packaging, configuration, testing, and deployment still need hardening.

## What The Project Does

At a high level, the project tries to:

1. Read a construction plan or blueprint PDF.
2. Extract text directly from the PDF or fall back to OCR.
3. Detect site conditions such as steep slopes, water buffers, or wetlands.
4. Query historical permit data stored in a local Chroma vector database.
5. Ask a local LLM to convert the blueprint context into structured construction tasks.
6. Save those generated tasks into PostgreSQL for later audit and review.

## Core Workflow

The current pipeline is centered around [`main.py`](./main.py):

1. `extract_text_fast(pdf_path)`
   Reads text from a PDF with `pdfplumber`; if the PDF has no text layer, it uses `pdf2image` and `pytesseract` to OCR each page.

2. `analyze_ground_hazards(text_data)`
   Applies simple keyword rules to classify risk:
   - `STEEP`, `15%`, `INCLINE`, `SLOPE` -> high slope risk
   - `STREAM`, `SURFACE WATER`, `BUFFER`, `WETLAND` -> environmental buffer risk

3. `cog_engine.refine_tasks_with_history(...)`
   Queries the Chroma collection `ground_knowledge`, retrieves similar historical records, then prompts an Ollama-served model (`llama3.2`) for a JSON task list.

4. PostgreSQL persistence
   Generated tasks are written into a `smart_tasks` table using SQLAlchemy.

## Repository Structure

```text
.
|-- README.md
|-- README.txt
|-- main.py
|-- accuracyvalidmain.py
|-- cog_engine.py
|-- query_os.py
|-- validate_accuracy.py
|-- test_cog.py
|-- train_all_data.py
|-- train_c_os.py
|-- generate_training_data.py
|-- engine.py
|-- manager.py
|-- alldbcodeinone.sql
|-- mem.txt
|-- safetynet.txt
|-- plan.pdf
|-- unnamed.png
|-- unnamed (1).png
|-- training_data/
|-- c_os_memory/
|-- chatgptaspect1.md
|-- For a software-only AI construction mana.md
`-- cons-trukt-os (3).ipynb
```

## File-By-File Guide

- `main.py`
  Primary orchestration script for extraction, hazard analysis, retrieval, LLM reasoning, and database insert.

- `accuracyvalidmain.py`
  Alternate version of the main flow with a post-generation safety override for slope stabilization tasks.

- `cog_engine.py`
  Retrieval-augmented reasoning layer. Connects to Chroma, queries historical permit memory, and calls Ollama for task JSON.

- `query_os.py`
  Simple query utility for inspecting the historical memory stored in Chroma.

- `train_all_data.py`
  Ingests training data from `training_data/` into Chroma. The current implementation reads only top-level files in that folder.

- `train_c_os.py`
  Ingests synthetic geotechnical data and industrial standards into Chroma.

- `generate_training_data.py`
  Generates synthetic slope-stability and WBS-standard seed files.

- `validate_accuracy.py`
  Pulls recent tasks from PostgreSQL and performs a few rule-based checks on the generated output.

- `test_cog.py`
  Lightweight integration-style script for checking that the cognitive layer returns task data.

- `engine.py`
  Separate prototype for blueprint parsing using Google GenAI. This is not integrated into the main flow.

- `manager.py`
  Stub for future downstream scheduling and rescheduling logic.

- `alldbcodeinone.sql`
  SQL schema draft for `smart_tasks`, `project_metadata`, and `audit_trail`.

- `mem.txt`
  Earlier exploratory schema and memory notes.

- `safetynet.txt`
  Solidity proof-of-concept for land or parcel assignment logic.

- `plan.pdf`
  Local example PDF used as the default plan input.

- `unnamed.png`, `unnamed (1).png`
  Local project images included from the source workspace.

- `chatgptaspect1.md`, `For a software-only AI construction mana.md`, `cons-trukt-os (3).ipynb`
  Research and ideation artifacts that capture the surrounding product vision.

## Included Data

This branch is intended to mirror the full local project, excluding only throwaway cache directories such as `__pycache__` and `.pytest_cache`.

Included data assets:

- `c_os_memory/`
  Local persisted Chroma database generated from historical permit data and used by the retrieval layer.

- `training_data/Boiler_Permits.csv`
- `training_data/Building_Permits.csv`
- `training_data/Building_Permits_Contacts.csv`
- `training_data/Construction_Permit_Boundary.csv`
- `training_data/Plan_Review.csv`
- `training_data/Plumbing_Permits.csv`
- `training_data/Plumbing_Permits_Contacts.csv`
  Raw and processed permit datasets from the local workspace.

- `training_data/archive (2).zip`
- `training_data/archive (4).zip`
- `training_data/archive (6).zip`
  Archived datasets preserved in the same folder layout used by the local project.

- `training_data/archive (2)/slope_stability_dataset.csv`
- `training_data/archive (4)/construction_dataset.csv`
- `training_data/archive (6)/Construction_Dataset.csv`
  Extracted smaller datasets used by training and experimentation.

## Git LFS Requirement

This repository uses Git LFS for the large datasets and binary artifacts. After cloning, run:

```bash
git lfs install
git lfs pull
```

Without `git lfs pull`, you will only see lightweight pointer files for the large datasets, memory database, PDF, and image assets.

## Dependencies

The repository does not yet ship with a `requirements.txt` or `pyproject.toml`, so dependencies must currently be installed manually.

### Python Packages

```bash
pip install chromadb ollama pdfplumber pytesseract pdf2image sqlalchemy pandas numpy pydantic google-genai pytest
```

### External Tools

- [Ollama](https://ollama.com/)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Poppler](https://poppler.freedesktop.org/)
- PostgreSQL

### Ollama Model

```bash
ollama pull llama3.2
```

## Configuration

The current codebase hard-codes machine-specific values inside the source files. Before running on a new machine, update these values:

- `POPPLER_PATH` in `main.py` and `accuracyvalidmain.py`
- `TESSERACT_EXE` in `main.py` and `accuracyvalidmain.py`
- `DB_URL` in `main.py`, `accuracyvalidmain.py`, and `validate_accuracy.py`
- `YOUR_API_KEY` in `engine.py`

Recommended future improvement: move all of these into environment variables or a `.env` file.

## How To Run

### 1. Generate Synthetic Seed Data

```bash
python generate_training_data.py
```

### 2. Build or Refresh Chroma Memory

```bash
python train_all_data.py
python train_c_os.py
```

### 3. Query Historical Memory

```bash
python query_os.py
```

### 4. Run The Main Pipeline

```bash
python main.py
```

### 5. Run The Alternate Pipeline

```bash
python accuracyvalidmain.py
```

### 6. Validate Recent Task Output

```bash
python validate_accuracy.py
```

### 7. Smoke-Test The Cognitive Layer

```bash
python test_cog.py
```

## Current Architecture Notes

The project currently mixes several prototype layers:

- Rule-based hazard classification
- Retrieval-augmented generation with Chroma + Ollama
- PostgreSQL task persistence
- Optional Google GenAI experimentation
- Synthetic data generation for geotechnical testing

That mix makes the repo useful for experimentation, but it also means the codebase is not yet normalized into packages, modules, or deployable services.

## Known Gaps And Limitations

These are important to know before using the system:

- `main.py` currently contains a broken line that references an undefined `response` variable after `cog_engine.refine_tasks_with_history(...)` already returns parsed JSON.
- The project is strongly tied to one machine's file paths and local services.
- There is no dependency lockfile or reproducible environment specification.
- `pytest` is not isolated from external dependencies, so test collection fails without local packages like `chromadb`.
- `train_all_data.py` only scans top-level files in `training_data/` and does not recurse into nested extracted folders.
- The previous README overstated the implementation and mentioned components not present in the current codebase.
- Secrets and connection strings should not remain hard-coded in source files.

## Suggested Next Improvements

If you continue developing this project, the next best steps are:

1. Add a `requirements.txt` or `pyproject.toml`.
2. Replace hard-coded paths and secrets with environment variables.
3. Fix the `main.py` task parsing bug.
4. Keep large datasets in Git LFS or move them to dedicated object storage.
5. Rework training ingestion to support nested datasets cleanly.
6. Add unit tests with mocks for Chroma, Ollama, and PostgreSQL.
7. Separate prototype research notes from the runnable application.

## Intended Output

When the full stack is available locally, the prototype should produce:

- extracted task lists with WBS-style codes
- risk annotations such as slope or buffer flags
- persisted `smart_tasks` rows in PostgreSQL
- memory-backed contextual task refinement based on similar permit history

## Important Disclaimer

This repository is an experimental construction-planning prototype. It should not be treated as a sealed engineering decision engine or a substitute for licensed professional review. Any real-world construction, permitting, geotechnical, or environmental decision should be validated by qualified human experts.
