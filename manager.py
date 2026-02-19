def auto_reschedule(task_id, delay_hours):
    # 1. Fetch task and its dependencies from PostgreSQL
    # 2. Shift the 'planned_end' date by delay_hours
    # 3. Use recursion to shift all 'child' tasks in the dependency graph
    # 4. Trigger an automated SMS notification to all affected subcontractors
    print(f"Alert: Task {task_id} delayed. Shifting downstream schedule...")
    pass