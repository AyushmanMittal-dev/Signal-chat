from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

# User Schemas
class RequestOTPRequest(BaseModel):
    phone: Optional[str] = None
    username: Optional[str] = None

class RequestOTPResponse(BaseModel):
    success: bool
    message: str

class VerifyOTPRequest(BaseModel):
    identifier: str  # phone or username
    otp: str

class ProfileSetupRequest(BaseModel):
    display_name: str
    avatar_url: Optional[str] = None
    about: Optional[str] = "Available"

class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    about: Optional[str] = None
    avatar_url: Optional[str] = None
    settings_json: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: Optional[str] = None
    username: Optional[str] = None
    display_name: str
    about: Optional[str] = None
    avatar_url: Optional[str] = None
    last_seen_at: datetime
    is_online: bool
    settings_json: Optional[str] = None
    created_at: datetime

class VerifyOTPResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user: UserResponse

# Contact Schemas
class AddContactRequest(BaseModel):
    identifier: str  # phone or username
    nickname: Optional[str] = None

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    contact_user_id: int
    nickname: Optional[str] = None
    contact_user: UserResponse
    created_at: datetime

# Reaction & Attachment Schemas
class ReactionRequest(BaseModel):
    emoji: str

class ReactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    user_id: int
    emoji: str

class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int
    file_url: str
    mime_type: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None

# Message Schemas
class MessageCreateRequest(BaseModel):
    client_id: Optional[str] = None
    type: str = "text"
    body: Optional[str] = None
    ciphertext: Optional[str] = None
    iv: Optional[str] = None
    sender_key_id: Optional[int] = None
    is_encrypted: bool = False
    reply_to_id: Optional[int] = None

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    sender_id: Optional[int] = None
    sender: Optional[UserResponse] = None
    client_id: Optional[str] = None
    type: str
    body: Optional[str] = None
    ciphertext: Optional[str] = None
    iv: Optional[str] = None
    sender_key_id: Optional[int] = None
    is_encrypted: bool = False
    reply_to_id: Optional[int] = None
    status: str
    expires_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime
    reactions: List[ReactionResponse] = []
    attachments: List[AttachmentResponse] = []

# Conversation Member & Conversation Schemas
class ConversationMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    user_id: int
    user: UserResponse
    role: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    last_read_message_id: Optional[int] = None
    is_muted: bool
    is_archived: bool

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_by: Optional[int] = None
    disappearing_seconds: Optional[int] = 0
    unread_count: int = 0
    last_message: Optional[MessageResponse] = None
    last_activity_at: datetime
    created_at: datetime
    members: List[ConversationMemberResponse] = []

class ConversationCreateRequest(BaseModel):
    user_id: int

class GroupCreateRequest(BaseModel):
    name: str
    avatar_url: Optional[str] = None
    member_ids: List[int]

class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class AddGroupMembersRequest(BaseModel):
    user_ids: List[int]

class UpdateMemberRoleRequest(BaseModel):
    role: str  # admin or member

class ConversationSettingsRequest(BaseModel):
    is_muted: Optional[bool] = None
    is_archived: Optional[bool] = None
    disappearing_seconds: Optional[int] = None

class MessageReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    user: UserResponse
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

class MessageInfoResponse(BaseModel):
    message_id: int
    status: str
    receipts: List[MessageReceiptResponse]

# Key, Block & Verification Schemas
class UserKeyRequest(BaseModel):
    public_key_jwk: str
    fingerprint: str

class UserKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    public_key_jwk: str
    fingerprint: str
    created_at: datetime

class BlockRequest(BaseModel):
    blocked_id: int

class BlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    blocker_id: int
    blocked_id: int
    blocked_user: UserResponse
    created_at: datetime

class ContactVerificationRequest(BaseModel):
    verified_fingerprint: str
