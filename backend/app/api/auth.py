from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas import LoginRequest, TokenResponse, UserResponse
from app.security import verify_password, create_access_token, get_current_user
from app.db import db_manager

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    users_col = db_manager.get_collection("users")
    user = users_col.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email address or password."
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")

    token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    user_dict = {
        "id": str(user.get("_id", "")),
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "department": user["department"],
        "faculty_id": user.get("faculty_id"),
        "is_active": user.get("is_active", True)
    }

    return TokenResponse(access_token=token, token_type="bearer", user=user_dict)

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        role=current_user["role"],
        department=current_user["department"],
        faculty_id=current_user.get("faculty_id"),
        is_active=current_user.get("is_active", True)
    )

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully."}
