from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Conversation, ConversationMember
from app.schemas.schemas import (
    GroupCreateRequest, GroupUpdateRequest, AddGroupMembersRequest,
    UpdateMemberRoleRequest, ConversationResponse, ConversationMemberResponse, UserResponse
)
from app.repositories import repo
from app.ws.manager import manager

router = APIRouter(prefix="/groups", tags=["Groups"])

def _check_admin(db: Session, conversation_id: int, user_id: int):
    member = repo.get_membership(db, conversation_id, user_id)
    if not member or member.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin privileges required for this action"}
        )
    return member

@router.post("", response_model=ConversationResponse)
async def create_group(
    payload: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not payload.name.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Group name is required")

    conv = repo.create_group_conversation(
        db, creator_id=current_user.id, name=payload.name.strip(),
        avatar_url=payload.avatar_url, member_ids=payload.member_ids
    )

    # Create system message
    repo.create_message(
        db, conversation_id=conv.id, sender_id=None,
        body=f"{current_user.display_name} created group '{conv.name}'", msg_type="system"
    )

    # Broadcast conversation created over WebSocket
    for m in conv.members:
        if m.user_id != current_user.id:
            await manager.send_to_user(m.user_id, {
                "type": "conversation.updated",
                "data": {"conversation_id": conv.id, "action": "created"}
            })

    from app.api.conversations import _build_conversation_response
    return _build_conversation_response(conv, current_user.id, db)

@router.get("/{id}/members", response_model=List[ConversationMemberResponse])
def get_group_members(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, id, current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    conv = repo.get_conversation_by_id(db, id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return [
        ConversationMemberResponse(
            id=m.id, conversation_id=m.conversation_id, user_id=m.user_id,
            user=UserResponse.model_validate(m.user), role=m.role,
            joined_at=m.joined_at, left_at=m.left_at,
            last_read_message_id=m.last_read_message_id,
            is_muted=m.is_muted, is_archived=m.is_archived
        )
        for m in conv.members if m.left_at is None
    ]

@router.post("/{id}/members")
async def add_group_members(
    id: int,
    payload: AddGroupMembersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(db, id, current_user.id)
    conv = repo.get_conversation_by_id(db, id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    added_names = []
    for uid in payload.user_ids:
        existing = repo.get_membership(db, id, uid)
        target_user = repo.get_user_by_id(db, uid)
        if target_user and not existing:
            m = ConversationMember(conversation_id=id, user_id=uid, role="member")
            db.add(m)
            added_names.append(target_user.display_name)

    db.commit()

    if added_names:
        names_str = ", ".join(added_names)
        repo.create_message(db, conversation_id=id, sender_id=None, body=f"{current_user.display_name} added {names_str}", msg_type="system")
        await manager.broadcast_to_conversation(db, conversation_id=id, message={"type": "member.added", "data": {"conversation_id": id, "user_ids": payload.user_ids}})

    return {"success": True, "added": len(added_names)}

@router.delete("/{id}/members/{user_id}")
async def remove_group_member(
    id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # User leaving or admin removing member
    if user_id != current_user.id:
        _check_admin(db, id, current_user.id)

    member = repo.get_membership(db, id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found in group")

    member.left_at = repo.utcnow()
    target_user = repo.get_user_by_id(db, user_id)
    name = target_user.display_name if target_user else "User"

    if user_id == current_user.id:
        sys_msg = f"{name} left the group"
    else:
        sys_msg = f"{current_user.display_name} removed {name}"

    repo.create_message(db, conversation_id=id, sender_id=None, body=sys_msg, msg_type="system")
    db.commit()

    await manager.broadcast_to_conversation(db, conversation_id=id, message={"type": "member.removed", "data": {"conversation_id": id, "user_id": user_id}})
    return {"success": True}

@router.patch("/{id}")
async def update_group(
    id: int,
    payload: GroupUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(db, id, current_user.id)
    conv = repo.get_conversation_by_id(db, id)
    if not conv or conv.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if payload.name:
        old_name = conv.name
        conv.name = payload.name.strip()
        repo.create_message(db, conversation_id=id, sender_id=None, body=f"{current_user.display_name} changed group name to '{conv.name}'", msg_type="system")
    if payload.avatar_url is not None:
        conv.avatar_url = payload.avatar_url

    db.commit()
    await manager.broadcast_to_conversation(db, conversation_id=id, message={"type": "conversation.updated", "data": {"conversation_id": id, "action": "renamed"}})
    return {"success": True}

@router.patch("/{id}/members/{user_id}/role")
def update_member_role(
    id: int,
    user_id: int,
    payload: UpdateMemberRoleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _check_admin(db, id, current_user.id)
    member = repo.get_membership(db, id, user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    member.role = payload.role
    db.commit()
    return {"success": True}
