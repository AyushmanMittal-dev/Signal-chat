import json
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import decode_access_token
from app.repositories import repo
from app.ws.manager import manager
from app.schemas.schemas import UserResponse, ReactionResponse

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4002, reason="Invalid token")
        return

    db: Session = SessionLocal()
    try:
        user = repo.get_user_by_id(db, user_id)
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return

        await manager.connect(user_id, websocket, db)

        while True:
            data_text = await websocket.receive_text()
            try:
                event = json.loads(data_text)
            except Exception:
                await websocket.send_json({"type": "error", "data": {"message": "Invalid JSON"}})
                continue

            event_type = event.get("type")
            payload = event.get("data", {})

            if event_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif event_type == "message.send":
                conversation_id = payload.get("conversation_id")
                client_id = payload.get("client_id")
                body = payload.get("body")
                ciphertext = payload.get("ciphertext")
                iv = payload.get("iv")
                is_encrypted = payload.get("is_encrypted", False)
                reply_to_id = payload.get("reply_to_id")

                member = repo.get_membership(db, conversation_id, user_id)
                if not member:
                    await websocket.send_json({"type": "error", "data": {"code": "FORBIDDEN", "message": "Not a member"}})
                    continue

                msg = repo.create_message(
                    db,
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    body=body,
                    client_id=client_id,
                    ciphertext=ciphertext,
                    iv=iv,
                    is_encrypted=is_encrypted,
                    reply_to_id=reply_to_id
                )

                # Send ack back to sender
                created_iso = msg.created_at.replace(tzinfo=timezone.utc).isoformat() if msg.created_at and msg.created_at.tzinfo is None else msg.created_at.isoformat()
                await websocket.send_json({
                    "type": "message.ack",
                    "data": {
                        "client_id": client_id,
                        "message_id": msg.id,
                        "created_at": created_iso,
                        "status": "sent"
                    }
                })

                # Broadcast message.new to online recipients
                from app.api.conversations import _build_message_response
                msg_resp = _build_message_response(msg).model_dump(mode="json")
                await manager.broadcast_to_conversation(
                    db, conversation_id=conversation_id,
                    message={"type": "message.new", "data": msg_resp},
                    exclude_user_id=user_id
                )

            elif event_type in ("typing.start", "typing.stop"):
                conversation_id = payload.get("conversation_id")
                is_typing = (event_type == "typing.start")
                await manager.broadcast_to_conversation(
                    db, conversation_id=conversation_id,
                    message={"type": "typing", "data": {"conversation_id": conversation_id, "user_id": user_id, "is_typing": is_typing}},
                    exclude_user_id=user_id
                )

            elif event_type == "message.delivered":
                message_id = payload.get("message_id")
                msg = db.query(repo.Message).filter(repo.Message.id == message_id).first()
                if msg:
                    # Update status
                    msg.status = "delivered"
                    db.commit()
                    await manager.send_to_user(
                        msg.sender_id,
                        {"type": "message.status", "data": {"message_id": message_id, "status": "delivered", "user_id": user_id}}
                    )

            elif event_type == "message.read":
                conversation_id = payload.get("conversation_id")
                up_to_message_id = payload.get("up_to_message_id")
                if conversation_id and up_to_message_id:
                    repo.mark_read(db, conversation_id, user_id, up_to_message_id)
                    await manager.broadcast_to_conversation(
                        db, conversation_id=conversation_id,
                        message={"type": "message.status", "data": {"conversation_id": conversation_id, "user_id": user_id, "up_to_message_id": up_to_message_id, "status": "read"}},
                        exclude_user_id=user_id
                    )

    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket, db)
    finally:
        db.close()
