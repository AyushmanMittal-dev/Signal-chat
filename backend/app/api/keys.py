from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, UserKey, ContactVerification
from app.schemas.schemas import UserKeyRequest, UserKeyResponse, ContactVerificationRequest
from app.repositories import repo
from app.ws.manager import manager

router = APIRouter(tags=["USP Keys & Verification"])

@router.put("/keys/me", response_model=UserKeyResponse)
async def register_public_key(
    payload: UserKeyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Revoke existing key if fingerprint changed
    existing_key = db.query(UserKey).filter(
        UserKey.user_id == current_user.id,
        UserKey.revoked_at.is_(None)
    ).first()

    key_changed = False
    if existing_key:
        if existing_key.fingerprint != payload.fingerprint:
            existing_key.revoked_at = repo.utcnow()
            key_changed = True

    new_key = UserKey(
        user_id=current_user.id,
        public_key_jwk=payload.public_key_jwk,
        fingerprint=payload.fingerprint
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)

    if key_changed:
        # Emit key.changed event to contacts
        contacts = repo.get_contacts_for_user(db, current_user.id)
        for c in contacts:
            await manager.send_to_user(c.contact_user_id, {
                "type": "key.changed",
                "data": {"user_id": current_user.id, "new_fingerprint": payload.fingerprint}
            })

    return UserKeyResponse.model_validate(new_key)

@router.get("/keys/{user_id}", response_model=UserKeyResponse)
def get_user_public_key(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = db.query(UserKey).filter(
        UserKey.user_id == user_id,
        UserKey.revoked_at.is_(None)
    ).order_by(UserKey.id.desc()).first()

    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No public key registered for user")

    return UserKeyResponse.model_validate(key)

@router.post("/contacts/{id}/verify")
def verify_safety_number(
    id: int,
    payload: ContactVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verification = db.query(ContactVerification).filter(
        ContactVerification.owner_id == current_user.id,
        ContactVerification.contact_user_id == id
    ).first()

    if verification:
        verification.verified_fingerprint = payload.verified_fingerprint
        verification.verified_at = repo.utcnow()
    else:
        verification = ContactVerification(
            owner_id=current_user.id,
            contact_user_id=id,
            verified_fingerprint=payload.verified_fingerprint
        )
        db.add(verification)

    db.commit()
    return {"success": True, "message": "Safety number verified"}

@router.delete("/contacts/{id}/verify")
def clear_safety_number_verification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verification = db.query(ContactVerification).filter(
        ContactVerification.owner_id == current_user.id,
        ContactVerification.contact_user_id == id
    ).first()

    if verification:
        db.delete(verification)
        db.commit()

    return {"success": True, "message": "Safety number verification cleared"}
