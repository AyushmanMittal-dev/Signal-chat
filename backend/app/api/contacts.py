from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User
from app.schemas.schemas import AddContactRequest, ContactResponse, UserResponse
from app.repositories import repo

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.get("", response_model=List[ContactResponse])
def list_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    contacts = repo.get_contacts_for_user(db, owner_id=current_user.id)
    return [
        ContactResponse(
            id=c.id,
            owner_id=c.owner_id,
            contact_user_id=c.contact_user_id,
            nickname=c.nickname,
            contact_user=UserResponse.model_validate(c.contact_user),
            created_at=c.created_at
        )
        for c in contacts
    ]

@router.post("", response_model=ContactResponse)
def add_contact(
    payload: AddContactRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = repo.get_user_by_phone_or_username(db, payload.identifier)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": f"User '{payload.identifier}' not found"}
        )
    if target.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "SELF_CONTACT", "message": "Cannot add yourself as a contact"}
        )

    contact = repo.add_contact(db, owner_id=current_user.id, contact_user_id=target.id, nickname=payload.nickname)
    return ContactResponse(
        id=contact.id,
        owner_id=contact.owner_id,
        contact_user_id=contact.contact_user_id,
        nickname=contact.nickname,
        contact_user=UserResponse.model_validate(contact.contact_user),
        created_at=contact.created_at
    )

@router.delete("/{contact_id}")
def remove_contact(
    contact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    success = repo.remove_contact(db, owner_id=current_user.id, contact_id=contact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CONTACT_NOT_FOUND", "message": "Contact not found"}
        )
    return {"success": True, "message": "Contact removed"}
