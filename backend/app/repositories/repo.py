from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from app.models.models import (
    User, Contact, Conversation, ConversationMember, Message,
    MessageReceipt, Reaction, Attachment, UserKey, Block, ContactVerification
)

def utcnow():
    return datetime.now(timezone.utc)

# User Repo
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_phone_or_username(db: Session, identifier: str) -> Optional[User]:
    clean = identifier.strip().lstrip("@")
    return db.query(User).filter(
        or_(User.phone == identifier, User.username == clean, User.username == identifier)
    ).first()

def create_user(db: Session, phone: Optional[str], username: Optional[str], display_name: str) -> User:
    if username:
        username = username.strip().lstrip("@")
    user = User(
        phone=phone,
        username=username,
        display_name=display_name,
        is_online=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def search_users(db: Session, query: str, exclude_user_id: int) -> List[User]:
    pattern = f"%{query.strip().lstrip('@')}%"
    return db.query(User).filter(
        User.id != exclude_user_id,
        or_(
            User.display_name.ilike(pattern),
            User.username.ilike(pattern),
            User.phone.ilike(pattern)
        )
    ).limit(20).all()

# Contact Repo
def get_contacts_for_user(db: Session, owner_id: int) -> List[Contact]:
    return db.query(Contact).filter(Contact.owner_id == owner_id).all()

def add_contact(db: Session, owner_id: int, contact_user_id: int, nickname: Optional[str] = None) -> Contact:
    existing = db.query(Contact).filter(
        Contact.owner_id == owner_id,
        Contact.contact_user_id == contact_user_id
    ).first()
    if existing:
        return existing
    contact = Contact(owner_id=owner_id, contact_user_id=contact_user_id, nickname=nickname)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact

def remove_contact(db: Session, owner_id: int, contact_id: int) -> bool:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.owner_id == owner_id).first()
    if contact:
        db.delete(contact)
        db.commit()
        return True
    return False

# Conversation & Member Repo
def get_user_memberships(db: Session, user_id: int) -> List[ConversationMember]:
    return db.query(ConversationMember).filter(
        ConversationMember.user_id == user_id,
        ConversationMember.left_at.is_(None)
    ).all()

def get_conversation_by_id(db: Session, conversation_id: int) -> Optional[Conversation]:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def get_membership(db: Session, conversation_id: int, user_id: int) -> Optional[ConversationMember]:
    return db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id,
        ConversationMember.left_at.is_(None)
    ).first()

def get_or_create_direct_conversation(db: Session, user1_id: int, user2_id: int) -> Conversation:
    if user1_id == user2_id:
        return get_or_create_note_to_self(db, user1_id)
    
    ids = sorted([user1_id, user2_id])
    direct_key = f"{ids[0]}_{ids[1]}"

    conv = db.query(Conversation).filter(Conversation.direct_key == direct_key).first()
    if not conv:
        conv = Conversation(type="direct", direct_key=direct_key, created_by=user1_id)
        db.add(conv)
        db.flush()

        m1 = ConversationMember(conversation_id=conv.id, user_id=user1_id, role="admin")
        m2 = ConversationMember(conversation_id=conv.id, user_id=user2_id, role="admin")
        db.add_all([m1, m2])
        db.commit()
        db.refresh(conv)
    return conv

def get_or_create_note_to_self(db: Session, user_id: int) -> Conversation:
    direct_key = f"note_{user_id}"
    conv = db.query(Conversation).filter(Conversation.direct_key == direct_key).first()
    if not conv:
        user = get_user_by_id(db, user_id)
        name = "Note to Self"
        conv = Conversation(type="note_to_self", name=name, direct_key=direct_key, created_by=user_id)
        db.add(conv)
        db.flush()

        m = ConversationMember(conversation_id=conv.id, user_id=user_id, role="admin")
        db.add(m)
        db.commit()
        db.refresh(conv)
    return conv

def create_group_conversation(db: Session, creator_id: int, name: str, avatar_url: Optional[str], member_ids: List[int]) -> Conversation:
    conv = Conversation(type="group", name=name, avatar_url=avatar_url, created_by=creator_id)
    db.add(conv)
    db.flush()

    all_ids = set([creator_id] + member_ids)
    for uid in all_ids:
        role = "admin" if uid == creator_id else "member"
        m = ConversationMember(conversation_id=conv.id, user_id=uid, role=role)
        db.add(m)
    db.commit()
    db.refresh(conv)
    return conv

def calculate_unread_count(db: Session, conversation_id: int, user_id: int) -> int:
    member = get_membership(db, conversation_id, user_id)
    if not member:
        return 0
    query = db.query(func.count(Message.id)).filter(
        Message.conversation_id == conversation_id,
        Message.sender_id != user_id,
        Message.created_at >= member.joined_at,
        Message.deleted_at.is_(None)
    )
    if member.last_read_message_id:
        query = query.filter(Message.id > member.last_read_message_id)
    return query.scalar() or 0

# Message & Receipt Repo
def create_message(
    db: Session,
    conversation_id: int,
    sender_id: Optional[int],
    body: Optional[str] = None,
    client_id: Optional[str] = None,
    msg_type: str = "text",
    ciphertext: Optional[str] = None,
    iv: Optional[str] = None,
    sender_key_id: Optional[int] = None,
    is_encrypted: bool = False,
    reply_to_id: Optional[int] = None,
    expires_at: Optional[datetime] = None
) -> Message:
    # Check client_id idempotency
    if client_id and sender_id:
        existing = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_id == sender_id,
            Message.client_id == client_id
        ).first()
        if existing:
            return existing

    msg = Message(
        conversation_id=conversation_id,
        sender_id=sender_id,
        client_id=client_id,
        type=msg_type,
        body=body,
        ciphertext=ciphertext,
        iv=iv,
        sender_key_id=sender_key_id,
        is_encrypted=is_encrypted,
        reply_to_id=reply_to_id,
        status="sent",
        expires_at=expires_at,
        created_at=utcnow()
    )
    db.add(msg)
    db.flush()

    # Update conversation last activity & last message
    conv = get_conversation_by_id(db, conversation_id)
    if conv:
        conv.last_message_id = msg.id
        conv.last_activity_at = msg.created_at

    # Create receipts for active recipients
    members = db.query(ConversationMember).filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.left_at.is_(None)
    ).all()

    for m in members:
        if sender_id is not None and m.user_id == sender_id:
            # Sender automatically read their own message
            m.last_read_message_id = msg.id
        else:
            receipt = MessageReceipt(message_id=msg.id, user_id=m.user_id)
            db.add(receipt)

    db.commit()
    db.refresh(msg)
    return msg

def get_messages(
    db: Session, conversation_id: int, before_id: Optional[int] = None, limit: int = 50
) -> List[Message]:
    query = db.query(Message).filter(
        Message.conversation_id == conversation_id,
        Message.deleted_at.is_(None)
    )
    if before_id:
        query = query.filter(Message.id < before_id)
    return query.order_by(desc(Message.id)).limit(limit).all()[::-1]  # Return in chronological order

def mark_read(db: Session, conversation_id: int, user_id: int, up_to_message_id: int):
    member = get_membership(db, conversation_id, user_id)
    if member:
        if not member.last_read_message_id or up_to_message_id > member.last_read_message_id:
            member.last_read_message_id = up_to_message_id
            db.flush()

    now = utcnow()
    # Update receipts
    unread_receipts = db.query(MessageReceipt).join(Message).filter(
        Message.conversation_id == conversation_id,
        MessageReceipt.user_id == user_id,
        MessageReceipt.read_at.is_(None),
        Message.id <= up_to_message_id
    ).all()

    for r in unread_receipts:
        r.read_at = now
        if not r.delivered_at:
            r.delivered_at = now

    db.commit()

# Block Repo
def block_user(db: Session, blocker_id: int, blocked_id: int) -> Block:
    existing = db.query(Block).filter(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id).first()
    if existing:
        return existing
    b = Block(blocker_id=blocker_id, blocked_id=blocked_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b

def unblock_user(db: Session, blocker_id: int, blocked_id: int) -> bool:
    b = db.query(Block).filter(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id).first()
    if b:
        db.delete(b)
        db.commit()
        return True
    return False

def is_blocked(db: Session, user1_id: int, user2_id: int) -> bool:
    return db.query(Block).filter(
        or_(
            and_(Block.blocker_id == user1_id, Block.blocked_id == user2_id),
            and_(Block.blocker_id == user2_id, Block.blocked_id == user1_id)
        )
    ).first() is not None
