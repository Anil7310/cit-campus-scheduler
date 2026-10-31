import re
from typing import Dict, Any

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"act\s+as\s+(an?\s+)?admin",
    r"i\s+am\s+(the\s+)?(admin|dean|director)",
    r"override\s+(all\s+)?permissions",
    r"approve\s+(this\s+)?booking\s+immediately",
    r"bypass\s+validation",
    r"grant\s+me\s+admin",
    r"drop\s+database",
    r"elevate\s+privilege"
]

def sanitize_user_input(text: str) -> str:
    cleaned = text
    for pattern in INJECTION_PATTERNS:
        cleaned = re.sub(pattern, "[FILTERED_ATTEMPT]", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def enforce_server_authority(extracted_dict: Dict[str, Any], user_role: str, user_faculty_id: str = None) -> Dict[str, Any]:
    """
    CRITICAL SECURITY CHECK:
    Overrides and strips any privileged field that an LLM or prompt injection might inject.
    Role and category are determined strictly by server-side context.
    """
    safe_data = extracted_dict.copy()
    
    # Strip dangerous keys
    for dangerous_key in ["is_approved", "approval_status", "override_constraints", "skip_validation", "priority_level"]:
        safe_data.pop(dangerous_key, None)

    # If the user is a club rep, they CANNOT set category to 'institute_event' unless authorized
    if user_role == "club" and safe_data.get("category") == "institute_event":
        safe_data["category"] = "club_event"

    return safe_data
