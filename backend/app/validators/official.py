import os
import sys
import json
import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger("cit_scheduler.official_validator")

def run_official_validator(cit_path: str, schedule_path: str, base_schedule_path: Optional[str] = None) -> Dict[str, Any]:
    possible_validator_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "starter-pack", "validator.py"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "validator.py"),
        "starter-pack/validator.py",
        "validator.py"
    ]
    
    val_path = None
    for p in possible_validator_paths:
        if os.path.exists(p):
            val_path = os.path.abspath(p)
            break

    if not val_path:
        raise FileNotFoundError("starter-pack/validator.py was not found.")

    cmd = [sys.executable, val_path, os.path.abspath(cit_path), os.path.abspath(schedule_path)]
    if base_schedule_path and os.path.exists(base_schedule_path):
        cmd.append(os.path.abspath(base_schedule_path))

    logger.info(f"Running official validator: {' '.join(cmd)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = proc.stdout.strip()
        if not output and proc.stderr:
            logger.error(f"Validator stderr: {proc.stderr}")
            return {
                "is_valid": False,
                "hard_violations_count": 1,
                "hard_violations": [f"Validator execution error: {proc.stderr[:300]}"],
                "soft_penalties": {"total_soft_penalty": 9999},
                "booking_score": 0,
                "moved_sessions_count": 0
            }
        
        parsed = json.loads(output)
        return parsed
    except Exception as e:
        logger.error(f"Exception running official validator: {e}")
        return {
            "is_valid": False,
            "hard_violations_count": 1,
            "hard_violations": [f"Validator failed to run: {str(e)}"],
            "soft_penalties": {"total_soft_penalty": 9999},
            "booking_score": 0,
            "moved_sessions_count": 0
        }
