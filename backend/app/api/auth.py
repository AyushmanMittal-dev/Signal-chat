from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import (
    RequestOTPRequest, RequestOTPResponse, VerifyOTPRequest, VerifyOTPResponse,
    ProfileSetupRequest, UserResponse
)
from app.repositories import repo

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/request-otp", response_model=RequestOTPResponse)
def request_otp(payload: RequestOTPRequest, db: Session = Depends(get_db)):
    if not payload.phone and not payload.username:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "VALIDATION_ERROR", "message": "Phone or username is required"}
        )
    return RequestOTPResponse(
        success=True,
        message="OTP sent to device. Use fixed OTP 123456 for testing."
    )

@router.post("/verify-otp", response_model=VerifyOTPResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    if payload.otp != settings.FIXED_OTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_OTP", "message": "Invalid OTP code. Use 123456."}
        )
    
    identifier = payload.identifier.strip()
    is_phone = identifier.startswith("+") or identifier.replace(" ", "").replace("-", "").isdigit()
    
    user = repo.get_user_by_phone_or_username(db, identifier)
    is_new_user = False

    if not user:
        is_new_user = True
        phone = identifier if is_phone else None
        username = None if is_phone else identifier.lstrip("@")
        display_name = identifier if is_phone else identifier.lstrip("@").capitalize()
        user = repo.create_user(db, phone=phone, username=username, display_name=display_name)
        # Auto-connect new user with existing users for immediate out-of-the-box liveness
        existing_users = db.query(User).filter(User.id != user.id).limit(10).all()
        for eu in existing_users:
            repo.add_contact(db, owner_id=user.id, contact_user_id=eu.id)
            repo.add_contact(db, owner_id=eu.id, contact_user_id=user.id)
            # Create direct conversation with Demo User (id=1)
            if eu.id == 1:
                repo.get_or_create_direct_conversation(db, user.id, eu.id)
    else:
        user.is_online = True
        db.commit()
        db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return VerifyOTPResponse(
        access_token=token,
        token_type="bearer",
        is_new_user=is_new_user,
        user=UserResponse.model_validate(user)
    )

@router.post("/profile", response_model=UserResponse)
def setup_profile(
    payload: ProfileSetupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.display_name = payload.display_name.strip()
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.about is not None:
        current_user.about = payload.about
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.is_online = False
    current_user.last_seen_at = repo.utcnow()
    db.commit()
    return {"success": True, "message": "Logged out successfully"}
