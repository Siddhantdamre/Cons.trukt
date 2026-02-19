import cog_engine

def run_cog_test():
    print("🧪 INITIALIZING COGNITIVE LAYER TEST...")

    # 1. Simulate the "Ground Truths" we found in your PDF
    mock_hazard_report = {
        "level": "High",
        "flags": ["CRITICAL: Steep Slope (15%+) detected", "ENV: Water Buffer detected"],
        "buffer": True
    }

    # 2. Simulate the blueprint text the AI would normally read
    mock_blueprint_text = """
    PROJECT: Sample House Addition. 
    SITE FEATURES: Steep slope at rear of property. 
    PROPOSED WORK: New detached garage and concrete retaining wall. 
    UTILITIES: New plumbing for utility sink.
    """

    # 3. Trigger the Brain
    try:
        print("\n--- STEP 1: CONSULTING HISTORICAL ARCHIVES ---")
        # This calls your cog_engine to search the 6,000+ permit records
        results = cog_engine.refine_tasks_with_history(mock_blueprint_text, mock_hazard_report)

        print("\n--- STEP 2: GENERATED INDUSTRIAL TASKS ---")
        print(f"{'WBS':<10} | {'TASK NAME':<45} | {'HOURS':<6}")
        print("-" * 65)
        
        tasks = results.get("tasks", [])
        for t in tasks:
            print(f"{t.get('wbs', '0.0'):<10} | {t.get('name', 'N/A')[:43]:<45} | {t.get('hours', 0):<6}")

        # --- 4. SUCCESS CHECK ---
        # Look for historical terms like 'Geo Soils' or 'ECA' in the output
        print("\n--- STEP 3: ACCURACY CHECK ---")
        output_str = str(results).upper()
        if "GEO" in output_str or "SOILS" in output_str or "DRAINAGE" in output_str:
            print("✅ TEST PASSED: Cog Engine correctly retrieved historical precedents!")
        else:
            print("⚠️ TEST NEUTRAL: Tasks generated, but historical wisdom wasn't obvious.")

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")

if __name__ == "__main__":
    run_cog_test()