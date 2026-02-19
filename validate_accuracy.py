import pandas as pd
from sqlalchemy import create_engine, text

# --- 1. CONFIGURATION ---
DB_URL = "postgresql://postgres:***REMOVED***@localhost:5432/c_os_db"
engine = create_engine(DB_URL)

def run_accuracy_audit():
    print("🕵️ Starting C-OS Accuracy Audit...")
    
    with engine.connect() as conn:
        # Fetch the latest tasks
        query = text("SELECT wbs_code, task_name, planned_hours, risk_level FROM smart_tasks ORDER BY id DESC LIMIT 10")
        df = pd.read_sql(query, conn)
        
    # --- 2. VALIDATION LOGIC ---
    errors = []
    
    # Check 1: The Incline Consequence
    # If the plan is High Risk, we MUST see stabilization tasks
    is_high_risk = any(df['risk_level'] == 'High')
    has_stabilization = any(df['task_name'].str.contains('Slope|Stabilization|Erosion', case=False))
    
    if is_high_risk and not has_stabilization:
        errors.append("❌ FAIL: High Risk detected but no Slope Stabilization task found.")
    else:
        print("✅ PASS: Ground Condition Risk matched with mitigation tasks.")

    # Check 2: Task Reality Check
    zero_hour_tasks = df[df['planned_hours'] <= 0]
    if not zero_hour_tasks.empty:
        errors.append(f"❌ FAIL: Found {len(zero_hour_tasks)} tasks with 0 man-hours.")
    else:
        print("✅ PASS: All tasks have valid man-hour estimates.")

    # Check 3: WBS Specificity
    # Professional WBS shouldn't be '0.0'
    generic_wbs = df[df['wbs_code'] == '0.0']
    if not generic_wbs.empty:
        errors.append("⚠️ WARNING: AI is using generic WBS codes (0.0). Check your prompt.")

    # --- 3. FINAL REPORT ---
    print("\n" + "="*40)
    print("📊 C-OS ACCURACY REPORT")
    print("="*40)
    if not errors:
        print("🌟 SYSTEM ACCURATE: Output matches industrial standards.")
    else:
        for err in errors:
            print(err)
    print("="*40)

if __name__ == "__main__":
    run_accuracy_audit()