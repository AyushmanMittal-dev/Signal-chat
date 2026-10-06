from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Conversation, ConversationMember, Message
from app.schemas.schemas import (
    ConversationResponse, ConversationMemberResponse, ConversationCreateRequest,
    MessageResponse, MessageCreateRequest, ConversationSettingsRequest, UserResponse,
    ReactionResponse, AttachmentResponse
)
from app.repositories import repo
from app.ws.manager import manager

router = APIRouter(prefix="/conversations", tags=["Conversations"])

def _build_message_response(msg: Message) -> MessageResponse:
    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        sender=UserResponse.model_validate(msg.sender) if msg.sender else None,
        client_id=msg.client_id,
        type=msg.type,
        body=msg.body,
        ciphertext=msg.ciphertext,
        iv=msg.iv,
        sender_key_id=msg.sender_key_id,
        is_encrypted=msg.is_encrypted,
        reply_to_id=msg.reply_to_id,
        status=msg.status,
        expires_at=msg.expires_at,
        deleted_at=msg.deleted_at,
        created_at=msg.created_at,
        reactions=[ReactionResponse.model_validate(r) for r in msg.reactions],
        attachments=[AttachmentResponse.model_validate(a) for a in msg.attachments]
    )

def _build_conversation_response(conv: Conversation, user_id: int, db: Session) -> ConversationResponse:
    unread = repo.calculate_unread_count(db, conv.id, user_id)
    last_msg = _build_message_response(conv.last_message) if conv.last_message else None
    
    # Format name for direct conversations if not group
    name = conv.name
    avatar_url = conv.avatar_url
    if conv.type == "direct":
        peer_member = next((m for m in conv.members if m.user_id != user_id), None)
        if peer_member and peer_member.user:
            name = peer_member.user.display_name
            avatar_url = peer_member.user.avatar_url

    members_resp = [
        ConversationMemberResponse(
            id=m.id,
            conversation_id=m.conversation_id,
            user_id=m.user_id,
            user=UserResponse.model_validate(m.user),
            role=m.role,
            joined_at=m.joined_at,
            left_at=m.left_at,
            last_read_message_id=m.last_read_message_id,
            is_muted=m.is_muted,
            is_archived=m.is_archived
        )
        for m in conv.members if m.left_at is None
    ]

    return ConversationResponse(
        id=conv.id,
        type=conv.type,
        name=name,
        avatar_url=avatar_url,
        created_by=conv.created_by,
        disappearing_seconds=conv.disappearing_seconds or 0,
        unread_count=unread,
        last_message=last_msg,
        last_activity_at=conv.last_activity_at,
        created_at=conv.created_at,
        members=members_resp
    )

@router.get("", response_model=List[ConversationResponse])
def list_conversations(
    q: Optional[str] = Query(None),
    filter: Optional[str] = Query("all"),  # all, unread, groups
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    memberships = repo.get_user_memberships(db, current_user.id)
    conv_ids = [m.conversation_id for m in memberships]
    
    if not conv_ids:
        return []

    convs = db.query(Conversation).filter(Conversation.id.in_(conv_ids)).order_by(Conversation.last_activity_at.desc()).all()
    results = []

    for conv in convs:
        resp = _build_conversation_response(conv, current_user.id, db)
        
        # Filtering
        if filter == "unread" and resp.unread_count == 0:
            continue
        if filter == "groups" and resp.type != "group":
            continue

        # Search matching
        if q:
            query_str = q.lower()
            name_match = resp.name and query_str in resp.name.lower()
            last_msg_match = resp.last_message and resp.last_message.body and query_str in resp.last_message.body.lower()
            if not name_match and not last_msg_match:
                continue

        results.append(resp)

    return results

@router.post("/note-to-self", response_model=ConversationResponse)
def get_or_create_note_to_self(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = repo.get_or_create_note_to_self(db, current_user.id)
    return _build_conversation_response(conv, current_user.id, db)

@router.post("", response_model=ConversationResponse)
def create_or_get_direct_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = repo.get_user_by_id(db, payload.user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "Target user not found"}
        )

    conv = repo.get_or_create_direct_conversation(db, current_user.id, target.id)
    return _build_conversation_response(conv, current_user.id, db)

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, conversation_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "You are not a member of this conversation"}
        )
    conv = repo.get_conversation_by_id(db, conversation_id)
    return _build_conversation_response(conv, current_user.id, db)

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_messages(
    conversation_id: int,
    before: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, conversation_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied to conversation history"}
        )

    msgs = repo.get_messages(db, conversation_id, before_id=before, limit=limit)
    return [_build_message_response(m) for m in msgs]

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: int,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, conversation_id, current_user.id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot send message to this conversation"}
        )

    # Check block status for direct chats
    conv = repo.get_conversation_by_id(db, conversation_id)
    if conv and conv.type == "direct":
        peer_member = next((m for m in conv.members if m.user_id != current_user.id), None)
        if peer_member and repo.is_blocked(db, current_user.id, peer_member.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "BLOCKED", "message": "You cannot message a blocked user"}
            )

    msg = repo.create_message(
        db,
        conversation_id=conversation_id,
        sender_id=current_user.id,
        body=payload.body,
        client_id=payload.client_id,
        msg_type=payload.type,
        ciphertext=payload.ciphertext,
        iv=payload.iv,
        sender_key_id=payload.sender_key_id,
        is_encrypted=payload.is_encrypted,
        reply_to_id=payload.reply_to_id
    )

    msg_resp = _build_message_response(msg)

    # WebSocket broadcast
    await manager.broadcast_to_conversation(
        db, conversation_id=conversation_id,
        message={"type": "message.new", "data": msg_resp.model_dump(mode="json")},
        exclude_user_id=current_user.id
    )

    return msg_resp

@router.post("/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    up_to_message_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, conversation_id, current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    repo.mark_read(db, conversation_id, current_user.id, up_to_message_id)
    
    # Notify sender of read receipt update over WebSocket
    await manager.broadcast_to_conversation(
        db, conversation_id=conversation_id,
        message={"type": "message.status", "data": {"conversation_id": conversation_id, "user_id": current_user.id, "up_to_message_id": up_to_message_id, "status": "read"}},
        exclude_user_id=current_user.id
    )
    return {"success": True}

@router.patch("/{conversation_id}/settings")
def update_conversation_settings(
    conversation_id: int,
    payload: ConversationSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = repo.get_membership(db, conversation_id, current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if payload.is_muted is not None:
        member.is_muted = payload.is_muted
    if payload.is_archived is not None:
        member.is_archived = payload.is_archived
    if payload.disappearing_seconds is not None:
        conv = repo.get_conversation_by_id(db, conversation_id)
        if conv:
            conv.disappearing_seconds = payload.disappearing_seconds

    db.commit()
    return {"success": True}
