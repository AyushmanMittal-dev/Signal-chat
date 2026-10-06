from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.models import User, Message, Reaction, MessageReceipt
from app.schemas.schemas import ReactionRequest, ReactionResponse, MessageInfoResponse, MessageReceiptResponse, UserResponse
from app.repositories import repo
from app.ws.manager import manager

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.delete("/{id}")
async def delete_message(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    member = repo.get_membership(db, msg.conversation_id, current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Only sender can delete for everyone
    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the sender can delete this message")

    msg.deleted_at = repo.utcnow()
    db.commit()

    await manager.broadcast_to_conversation(
        db, conversation_id=msg.conversation_id,
        message={"type": "message.deleted", "data": {"message_id": id, "conversation_id": msg.conversation_id}}
    )
    return {"success": True}

@router.put("/{id}/reaction", response_model=ReactionResponse)
async def set_reaction(
    id: int,
    payload: ReactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    member = repo.get_membership(db, msg.conversation_id, current_user.id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    reaction = db.query(Reaction).filter(Reaction.message_id == id, Reaction.user_id == current_user.id).first()
    if reaction:
        reaction.emoji = payload.emoji
    else:
        reaction = Reaction(message_id=id, user_id=current_user.id, emoji=payload.emoji)
        db.add(reaction)

    db.commit()
    db.refresh(reaction)

    reactions = db.query(Reaction).filter(Reaction.message_id == id).all()
    reactions_data = [ReactionResponse.model_validate(r).model_dump(mode="json") for r in reactions]

    await manager.broadcast_to_conversation(
        db, conversation_id=msg.conversation_id,
        message={"type": "reaction.updated", "data": {"message_id": id, "reactions": reactions_data}}
    )
    return ReactionResponse.model_validate(reaction)

@router.delete("/{id}/reaction")
async def remove_reaction(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reaction = db.query(Reaction).filter(Reaction.message_id == id, Reaction.user_id == current_user.id).first()
    if reaction:
        db.delete(reaction)
        db.commit()

        msg = db.query(Message).filter(Message.id == id).first()
        if msg:
            reactions = db.query(Reaction).filter(Reaction.message_id == id).all()
            reactions_data = [ReactionResponse.model_validate(r).model_dump(mode="json") for r in reactions]
            await manager.broadcast_to_conversation(
                db, conversation_id=msg.conversation_id,
                message={"type": "reaction.updated", "data": {"message_id": id, "reactions": reactions_data}}
            )
    return {"success": True}

@router.get("/{id}/info", response_model=MessageInfoResponse)
def get_message_info(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(Message).filter(Message.id == id).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only sender can view message info panel")

    receipts = db.query(MessageReceipt).filter(MessageReceipt.message_id == id).all()
    receipts_resp = [
        MessageReceiptResponse(
            user_id=r.user_id,
            user=UserResponse.model_validate(r.user),
            delivered_at=r.delivered_at,
            read_at=r.read_at
        )
        for r in receipts
    ]

    return MessageInfoResponse(
        message_id=msg.id,
        status=msg.status,
        receipts=receipts_resp
    )
