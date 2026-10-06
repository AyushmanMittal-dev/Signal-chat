import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import UserResponse, UserUpdateRequest
from app.repositories import repo

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.display_name is not None:
        current_user.display_name = payload.display_name.strip()
    if payload.about is not None:
        current_user.about = payload.about.strip()
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url
    if payload.settings_json is not None:
        current_user.settings_json = json.dumps(payload.settings_json)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.get("/search", response_model=List[UserResponse])
def search_users(
    q: str = Query("", min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    users = repo.search_users(db, query=q, exclude_user_id=current_user.id)
    return [UserResponse.model_validate(u) for u in users]
