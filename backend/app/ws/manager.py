from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.models import User, ConversationMember

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> set of active WebSocket instances
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket, db: Session):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
            # User became online
            self._update_user_presence(db, user_id, is_online=True)
            await self._broadcast_presence_change(db, user_id, is_online=True)
        self.active_connections[user_id].add(websocket)

    async def disconnect(self, user_id: int, websocket: WebSocket, db: Session):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # User went offline
                now = datetime.now(timezone.utc)
                self._update_user_presence(db, user_id, is_online=False, last_seen_at=now)
                await self._broadcast_presence_change(db, user_id, is_online=False, last_seen_at=now)

    def _update_user_presence(self, db: Session, user_id: int, is_online: bool, last_seen_at: Optional[datetime] = None):
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_online = is_online
            if last_seen_at:
                user.last_seen_at = last_seen_at
            db.commit()

    async def _broadcast_presence_change(self, db: Session, user_id: int, is_online: bool, last_seen_at: Optional[datetime] = None):
        payload = {
            "type": "presence",
            "data": {
                "user_id": user_id,
                "is_online": is_online,
                "last_seen_at": (last_seen_at or datetime.now(timezone.utc)).isoformat()
            }
        }
        # Find all users who share a conversation with this user
        member_convs = db.query(ConversationMember.conversation_id).filter(
            ConversationMember.user_id == user_id,
            ConversationMember.left_at.is_(None)
        ).subquery()
        
        peer_user_ids = db.query(ConversationMember.user_id).filter(
            ConversationMember.conversation_id.in_(member_convs),
            ConversationMember.user_id != user_id
        ).distinct().all()

        for (peer_id,) in peer_user_ids:
            await self.send_to_user(peer_id, payload)

    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            sockets = list(self.active_connections[user_id])
            for ws in sockets:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass

    async def broadcast_to_conversation(
        self, db: Session, conversation_id: int, message: dict, exclude_user_id: Optional[int] = None
    ):
        members = db.query(ConversationMember.user_id).filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.left_at.is_(None)
        ).all()

        for (member_id,) in members:
            if exclude_user_id and member_id == exclude_user_id:
                continue
            await self.send_to_user(member_id, message)

manager = ConnectionManager()
