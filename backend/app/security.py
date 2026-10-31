import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.db import db_manager

logger = logging.getLogger("cit_scheduler.security")

import bcrypt
security_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8")[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or token is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims.")
    
    users_col = db_manager.get_collection("users")
    user = users_col.find_one({"email": email})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or disabled.")
    
    # Return user dict (convert _id to str)
    user["id"] = str(user.get("_id", ""))
    return user

def require_role(allowed_roles: List[str]):
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of roles {allowed_roles}, but current user has role '{user_role}'."
            )
        return current_user
    return role_checker

def check_not_self_approval(requester_id: str, decider_id: str, action: str = "approve"):
    if str(requester_id) == str(decider_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Conflict of interest: You cannot {action} your own request."
        )

# Seed demo accounts if not present
def seed_demo_users():
    users_col = db_manager.get_collection("users")
    demo_users = [
        {
            "name": "Prof. S. R. Verma (Dean Academics)",
            "email": "admin@cit.edu",
            "password_hash": get_password_hash("Admin@123"),
            "role": "admin",
            "department": "Dean's Office",
            "faculty_id": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "name": "Dr. R. K. Mohapatra (CSE Coordinator)",
            "email": "coordinator@cit.edu",
            "password_hash": get_password_hash("Coord@123"),
            "role": "coordinator",
            "department": "CSE",
            "faculty_id": "F01",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "name": "Dr. A. Sharma (CSE Faculty)",
            "email": "faculty@cit.edu",
            "password_hash": get_password_hash("Faculty@123"),
            "role": "faculty",
            "department": "CSE",
            "faculty_id": "F01", # Real faculty in dataset with sessions!
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "name": "Vikram Seth (Robotics & Spectra Rep)",
            "email": "club@cit.edu",
            "password_hash": get_password_hash("Club@123"),
            "role": "club",
            "department": "Student Council",
            "faculty_id": None,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]

    for u in demo_users:
        existing = users_col.find_one({"email": u["email"]})
        if not existing:
            users_col.insert_one(u)
            logger.info(f"Seeded demo user: {u['email']} ({u['role']})")
