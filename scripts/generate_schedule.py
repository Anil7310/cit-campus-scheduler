import os
import sys
import json
from datetime import datetime, timezone

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.model_timetable import TimetableSolver
from app.validators.hard import validate_hard_constraints
from app.validators.official import run_official_validator

def main():
    print("=== CIT SCHEDULER: GENERATE BASELINE TIMETABLE ===")
    dataset = load_default_dataset()
    print(f"Loaded dataset: {len(dataset.rooms)} rooms, {len(dataset.faculty)} faculty, {len(dataset.sessions)} sessions.")

    solver = TimetableSolver(dataset, time_limit_seconds=60, num_workers=2)
    status_str, assignments, metrics = solver.solve()
    print(f"Solver Status: {status_str}")
    print(f"Assigned Sessions: {len(assignments)}")
    print(f"Metrics: {metrics}")

    if status_str not in ("OPTIMAL", "FEASIBLE") or len(assignments) != len(dataset.sessions):
        print("ERROR: Failed to find complete feasible timetable!")
        sys.exit(1)

    # 1. Check with internal hard validator
    hard_result = validate_hard_constraints(dataset, assignments)
    print(f"\nInternal Hard Validator Result: valid={hard_result['is_valid']}, violations={hard_result['violations_count']}")
    if not hard_result["is_valid"]:
        for v in hard_result["violations"][:10]:
            print(f"  [X] {v}")
        sys.exit(1)

    # 2. Write to exports/schedule.json
    os.makedirs("exports", exist_ok=True)
    schedule_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_version": dataset.metadata.get("version", "1.0.0"),
            "solver_status": status_str,
            "metrics": metrics
        },
        "timetable": assignments,
        "exams": [],
        "bookings": []
    }

    schedule_path = "exports/schedule.json"
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, indent=2)
    print(f"\nSaved export to {schedule_path}")

    # 3. Check with official validator
    cit_path = "starter-pack/cit_public.json"
    val_report = run_official_validator(cit_path, schedule_path)
    print("\n=== OFFICIAL VALIDATOR EVALUATION ===")
    print(f"Valid: {val_report.get('is_valid')}")
    print(f"Hard Violations: {val_report.get('hard_violations_count')}")
    print(f"Total Soft Penalty: {val_report.get('soft_penalties', {}).get('total_soft_penalty')}")
    print(f"Soft Penalty Breakdown: {json.dumps(val_report.get('soft_penalties', {}), indent=2)}")

    if val_report.get("is_valid"):
        print("\n>>> GATE A PASSED: 0 Hard Violations achieved! <<<")
        sys.exit(0)
    else:
        print("\n>>> GATE A FAILED: Hard violations detected: <<<")
        for v in val_report.get("hard_violations", []):
            print(f"  [X] {v}")
        sys.exit(1)

if __name__ == "__main__":
    main()
