import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.model_timetable import TimetableSolver
from app.scheduler.model_exams import ExamScheduler
from app.scheduler.model_booking import BookingDecisionEngine
from app.validators.hard import validate_hard_constraints
from app.validators.official import run_official_validator

def main():
    print("=== CIT SCHEDULER: GENERATE COMPLETE SCHEDULE (TIMETABLE + EXAMS + BOOKINGS) ===")
    dataset = load_default_dataset()
    print(f"Loaded dataset: {len(dataset.rooms)} rooms, {len(dataset.faculty)} faculty, {len(dataset.sessions)} sessions, {len(dataset.exams)} exams, {len(dataset.booking_requests)} booking requests.")

    # 1. Timetable Solve
    solver = TimetableSolver(dataset, time_limit_seconds=60, num_workers=2)
    status_str, assignments, metrics = solver.solve()
    print(f"\n[1] Timetable Solver Status: {status_str} ({len(assignments)} sessions)")

    # 2. Exam Solve
    exam_solver = ExamScheduler(dataset)
    exam_assignments = exam_solver.solve()
    print(f"[2] Exam Scheduler: Scheduled {len(exam_assignments)} midsem exams")

    # 3. Booking Engine Solve
    booking_engine = BookingDecisionEngine(dataset, assignments)
    booking_decisions = booking_engine.decide_all()
    print(f"[3] Booking Decision Engine: Processed {len(booking_decisions)} Spectra booking requests")
    approved = sum(1 for b in booking_decisions if b["decision"] == "approved")
    alt = sum(1 for b in booking_decisions if b["decision"] == "alternative_offered")
    rejected = sum(1 for b in booking_decisions if b["decision"] == "rejected")
    print(f"    Approved: {approved}, Alternatives Offered: {alt}, Rejected: {rejected}")

    # Build schedule_data
    schedule_data = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_version": dataset.metadata.get("version", "1.0.0"),
            "solver_status": status_str,
            "metrics": metrics
        },
        "timetable": assignments,
        "exams": exam_assignments,
        "bookings": booking_decisions
    }

    os.makedirs("exports", exist_ok=True)
    schedule_path = "exports/schedule.json"
    with open(schedule_path, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, indent=2)
    print(f"\nSaved complete schedule export to {schedule_path}")

    # Run official validator
    cit_path = "starter-pack/cit_public.json"
    report = run_official_validator(cit_path, schedule_path)
    print("\n=== OFFICIAL VALIDATOR EVALUATION (GATE B) ===")
    print(f"Valid: {report.get('is_valid')}")
    print(f"Hard Violations: {report.get('hard_violations_count')}")
    print(f"Booking Score: {report.get('booking_score')}")
    print(f"Total Soft Penalty: {report.get('soft_penalties', {}).get('total_soft_penalty')}")

    if report.get("is_valid"):
        print("\n>>> GATE B PASSED: 0 Hard Violations for Timetable, Exams & Bookings! <<<")
        sys.exit(0)
    else:
        print("\n>>> GATE B FAILED: Violations detected: <<<")
        for v in report.get("hard_violations", []):
            print(f"  [X] {v}")
        sys.exit(1)

if __name__ == "__main__":
    main()
