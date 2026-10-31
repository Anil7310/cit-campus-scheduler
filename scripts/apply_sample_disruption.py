import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.repair import ReschedulingEngine
from app.validators.official import run_official_validator

def main():
    print("=== CIT SCHEDULER: APPLY DISRUPTION & RESCHEDULE (GATE C) ===")
    
    # 1. Load base schedule
    base_schedule_path = "exports/schedule.json"
    if not os.path.exists(base_schedule_path):
        print(f"Error: Base schedule {base_schedule_path} not found. Please run generate_schedule.py first.")
        sys.exit(1)

    with open(base_schedule_path, "r", encoding="utf-8") as f:
        base_schedule_data = json.load(f)

    base_assignments = base_schedule_data.get("timetable", [])
    print(f"Loaded base schedule with {len(base_assignments)} assignments.")

    # 2. Load sample disruption
    disruption_path = "starter-pack/sample_disruption.json"
    with open(disruption_path, "r", encoding="utf-8") as f:
        disruption_data = json.load(f)

    disruptions = disruption_data.get("disruptions", [])
    print(f"Loaded {len(disruptions)} disruptions:")
    for d in disruptions:
        print(f"  - {d.get('type')}: {d.get('reason')}")

    dataset = load_default_dataset()
    engine = ReschedulingEngine(dataset, base_assignments)
    
    print("\nSolving rescheduling repair problem with minimal move objective...")
    result = engine.apply_disruptions(disruptions, time_limit_seconds=30)
    print(f"Solver Status: {result.get('status')}")
    print(f"Moved Sessions Count: {result.get('moved_count')}")
    print(f"Diff Items: {len(result.get('diff', []))}")
    for item in result.get("diff", []):
        sid = item.get("session_id")
        cc = item.get("course_code")
        old = item.get("old")
        new = item.get("new")
        print(f"  * {sid} ({cc}): {old} -> {new} | Reason: {item.get('reason')}")

    if result.get("status") not in ("OPTIMAL", "FEASIBLE"):
        print("ERROR: Rescheduling was infeasible!")
        sys.exit(1)

    # Save exports/schedule_after.json
    schedule_after_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "base_version": "1.0.0",
            "disruptions_applied": len(disruptions),
            "moved_sessions_count": result.get("moved_count"),
            "solver_status": result.get("status")
        },
        "disruptions": disruptions,
        "timetable": result.get("schedule", []),
        "exams": base_schedule_data.get("exams", []),
        "bookings": base_schedule_data.get("bookings", []),
        "diff": result.get("diff", [])
    }

    schedule_after_path = "exports/schedule_after.json"
    with open(schedule_after_path, "w", encoding="utf-8") as f:
        json.dump(schedule_after_data, f, indent=2)
    print(f"\nSaved exports/schedule_after.json")

    # Run official validator comparing schedule_after with cit_public.json and base_schedule.json
    cit_path = "starter-pack/cit_public.json"
    report = run_official_validator(cit_path, schedule_after_path, base_schedule_path)
    print("\n=== OFFICIAL VALIDATOR EVALUATION (GATE C) ===")
    print(f"Valid: {report.get('is_valid')}")
    print(f"Hard Violations: {report.get('hard_violations_count')}")
    print(f"Moved Sessions Count: {report.get('moved_sessions_count')}")
    print(f"Total Soft Penalty: {report.get('soft_penalties', {}).get('total_soft_penalty')}")

    if report.get("is_valid") and report.get("moved_sessions_count", 0) <= 5:
        print(f"\n>>> GATE C PASSED: 0 Hard Violations and minimal moved sessions ({report.get('moved_sessions_count')})! <<<")
        sys.exit(0)
    else:
        print("\n>>> GATE C FAILED: Violations or excessive moves detected: <<<")
        for v in report.get("hard_violations", []):
            print(f"  [X] {v}")
        sys.exit(1)

if __name__ == "__main__":
    main()
