import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.security import get_current_user, require_role, check_not_self_approval
from app.db import db_manager
from app.schemas import DisruptionProposalCreate
from app.scheduler.dataset_adapter import load_default_dataset
from app.scheduler.repair import ReschedulingEngine
from app.scheduler.diagnostics import diagnose_session_infeasibility
from app.validators.hard import validate_hard_constraints

logger = logging.getLogger("cit_scheduler.rescheduling_api")
router = APIRouter(prefix="/rescheduling", tags=["Rescheduling"])

@router.post("/propose")
def propose_rescheduling(
    payload: DisruptionProposalCreate,
    current_user: dict = Depends(get_current_user)
):
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    proposals_col = db_manager.get_collection("proposals")

    # Get published timetable
    state = state_col.find_one({"_id": "state"})
    pub_ver = state.get("published_version") if state else None
    t = timetables_col.find_one({"version": pub_ver}) if pub_ver else timetables_col.find_one({})

    if not t:
        raise HTTPException(status_code=400, detail="No published timetable available to base repairs on.")

    base_version = t.get("version", 1)
    base_assignments = t.get("assignments", [])

    ds = load_default_dataset()
    engine = ReschedulingEngine(ds, base_assignments)

    disruption_dicts = [d.dict() for d in payload.disruptions]
    res = engine.apply_disruptions(disruption_dicts, time_limit_seconds=30)

    proposal_id = f"PROP_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    diagnostics_info = []
    if res["status"] in ("INFEASIBLE", "UNKNOWN"):
        # Run diagnostics on affected sessions
        for s in ds.sessions:
            diag = diagnose_session_infeasibility(s, ds, disruption_dicts)
            if diag["valid_candidate_slots"] == 0:
                diagnostics_info.append(diag)

    # Validate proposed schedule if feasible
    hard_val = {"is_valid": False, "violations": []}
    if res["status"] in ("OPTIMAL", "FEASIBLE") and res.get("schedule"):
        hard_val = validate_hard_constraints(ds, res["schedule"])

    proposal_doc = {
        "_id": proposal_id,
        "base_version": base_version,
        "disruptions": disruption_dicts,
        "solver_status": res["status"],
        "moved_count": res.get("moved_count", 0),
        "diff": res.get("diff", []),
        "proposed_schedule": res.get("schedule", []),
        "validation": hard_val,
        "diagnostics": diagnostics_info,
        "status": "pending",
        "created_by": current_user["id"],
        "created_by_email": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    proposals_col.insert_one(proposal_doc)
    return proposal_doc

@router.get("/proposals")
def list_proposals():
    proposals_col = db_manager.get_collection("proposals")
    proposals = proposals_col.find().sort("created_at", -1).to_list(50)
    for p in proposals:
        p["id"] = str(p.get("_id", ""))
    return proposals

@router.post("/proposals/{proposal_id}/approve")
def approve_proposal(
    proposal_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    proposals_col = db_manager.get_collection("proposals")
    timetables_col = db_manager.get_collection("timetables")
    state_col = db_manager.get_collection("system_state")
    audit_col = db_manager.get_collection("audit_logs")

    proposal = proposals_col.find_one({"_id": proposal_id})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    if proposal.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.get('status')}.")

    # No self approval
    check_not_self_approval(proposal.get("created_by"), current_user["id"], action="approve")

    # Optimistic locking: verify base_version has not changed
    state = state_col.find_one({"_id": "state"})
    current_pub_ver = state.get("published_version") if state else None
    if current_pub_ver != proposal.get("base_version"):
        proposals_col.update_one({"_id": proposal_id}, {"$set": {"status": "stale"}})
        raise HTTPException(
            status_code=409,
            detail=f"Proposal is stale! Current published timetable is version {current_pub_ver}, but proposal was based on version {proposal.get('base_version')}. Please re-generate."
        )

    # Save new timetable version
    last_t = timetables_col.find().sort("version", -1).limit(1).to_list()
    new_version = (last_t[0]["version"] + 1) if last_t else 1

    t_doc = {
        "version": new_version,
        "status": "published",
        "dataset_version": "1.0.0",
        "assignments": proposal["proposed_schedule"],
        "base_version": proposal["base_version"],
        "diff": proposal["diff"],
        "created_by": current_user["email"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    timetables_col.insert_one(t_doc)

    # Update system state & proposal
    state_col.update_one({"_id": "state"}, {"$set": {"published_version": new_version}})
    proposals_col.update_one(
        {"_id": proposal_id},
        {"$set": {
            "status": "approved",
            "decided_by": current_user["email"],
            "published_version": new_version,
            "decided_at": datetime.now(timezone.utc).isoformat()
        }}
    )

    # Audit log
    audit_col.insert_one({
        "actor_id": current_user["id"],
        "actor_email": current_user["email"],
        "action": "approve_reschedule_proposal",
        "entity": "proposal",
        "entity_id": proposal_id,
        "details": {"new_version": new_version, "moved_sessions": proposal.get("moved_count", 0)},
        "ts": datetime.now(timezone.utc).isoformat()
    })

    return {
        "message": f"Proposal approved! New timetable version {new_version} published with {proposal.get('moved_count', 0)} moved sessions.",
        "version": new_version
    }

@router.post("/proposals/{proposal_id}/reject")
def reject_proposal(
    proposal_id: str,
    current_user: dict = Depends(require_role(["admin"]))
):
    proposals_col = db_manager.get_collection("proposals")
    proposal = proposals_col.find_one({"_id": proposal_id})
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found.")

    check_not_self_approval(proposal.get("created_by"), current_user["id"], action="reject")

    proposals_col.update_one(
        {"_id": proposal_id},
        {"$set": {
            "status": "rejected",
            "decided_by": current_user["email"],
            "decided_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Proposal rejected."}
