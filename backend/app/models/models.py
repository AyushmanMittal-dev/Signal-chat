from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True, nullable=True)
    display_name = Column(String, nullable=False)
    about = Column(String, nullable=True, default="Available")
    avatar_url = Column(String, nullable=True)
    last_seen_at = Column(DateTime, default=utcnow)
    is_online = Column(Boolean, default=False)
    settings_json = Column(
        Text,
        default='{"hide_previews": false, "read_receipts": true, "typing_indicators": true, "screen_lock_minutes": 0}'
    )
    created_at = Column(DateTime, default=utcnow)

    # Relationships
    contacts_owned = relationship("Contact", foreign_keys="Contact.owner_id", back_populates="owner", cascade="all, delete-orphan")
    memberships = relationship("ConversationMember", back_populates="user", cascade="all, delete-orphan")
    keys = relationship("UserKey", back_populates="user", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    nickname = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("owner_id", "contact_user_id", name="uq_owner_contact"),
    )

    owner = relationship("User", foreign_keys=[owner_id], back_populates="contacts_owned")
    contact_user = relationship("User", foreign_keys=[contact_user_id])


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False, default="direct")  # direct, group, note_to_self
    name = Column(String, nullable=True)  # Group only
    avatar_url = Column(String, nullable=True)  # Group only
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    direct_key = Column(String, unique=True, nullable=True)  # "minId_maxId" for direct chats
    disappearing_seconds = Column(Integer, nullable=True, default=0)
    last_message_id = Column(Integer, ForeignKey("messages.id", use_alter=True, name="fk_conv_last_msg"), nullable=True)
    last_activity_at = Column(DateTime, default=utcnow, index=True)
    created_at = Column(DateTime, default=utcnow)

    members = relationship("ConversationMember", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", foreign_keys="Message.conversation_id", back_populates="conversation", cascade="all, delete-orphan")
    last_message = relationship("Message", foreign_keys=[last_message_id], post_update=True)


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False, default="member")  # admin, member
    joined_at = Column(DateTime, default=utcnow)
    left_at = Column(DateTime, nullable=True)
    last_read_message_id = Column(Integer, ForeignKey("messages.id", use_alter=True, name="fk_member_last_read"), nullable=True)
    is_muted = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conv_user"),
    )

    conversation = relationship("Conversation", back_populates="members")
    user = relationship("User", back_populates="memberships")
    last_read_message = relationship("Message", foreign_keys=[last_read_message_id], post_update=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for system messages
    client_id = Column(String, nullable=True, index=True)
    type = Column(String, nullable=False, default="text")  # text, system, image, file
    body = Column(Text, nullable=True)
    ciphertext = Column(Text, nullable=True)
    iv = Column(Text, nullable=True)
    sender_key_id = Column(Integer, ForeignKey("user_keys.id"), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    reply_to_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    status = Column(String, nullable=False, default="sent")  # sent, delivered, read
    expires_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)

    __table_args__ = (
        Index("idx_msg_conv_created", "conversation_id", "created_at"),
    )

    conversation = relationship("Conversation", foreign_keys=[conversation_id], back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("Message", remote_side=[id])
    receipts = relationship("MessageReceipt", back_populates="message", cascade="all, delete-orphan")
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="message", cascade="all, delete-orphan")


class MessageReceipt(Base):
    __tablename__ = "message_receipts"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Recipient
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_msg_recipient"),
        Index("idx_receipt_user_read", "user_id", "read_at"),
    )

    message = relationship("Message", back_populates="receipts")
    user = relationship("User", foreign_keys=[user_id])


class Reaction(Base):
    __tablename__ = "reactions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    emoji = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_msg_user_reaction"),
    )

    message = relationship("Message", back_populates="reactions")
    user = relationship("User", foreign_keys=[user_id])


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    file_url = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)

    message = relationship("Message", back_populates="attachments")


class UserKey(Base):
    __tablename__ = "user_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    public_key_jwk = Column(Text, nullable=False)
    fingerprint = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    revoked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint", name="uq_user_fingerprint"),
    )

    user = relationship("User", back_populates="keys")


class Block(Base):
    __tablename__ = "blocks"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blocked_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_blocker_blocked"),
    )


class ContactVerification(Base):
    __tablename__ = "contact_verifications"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    verified_fingerprint = Column(String, nullable=False)
    verified_at = Column(DateTime, default=utcnow)

    __table_args__ = (
        UniqueConstraint("owner_id", "contact_user_id", name="uq_owner_verified_contact"),
    )
