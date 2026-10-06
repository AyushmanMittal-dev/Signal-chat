from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.models import (
    User, Contact, Conversation, ConversationMember, Message, MessageReceipt, Reaction
)

def seed_database(db: Session):
    # Check if users already exist
    if db.query(User).first() is not None:
        print("[SEED] Database already contains data. Skipping seed.")
        return

    print("[SEED] Seeding database with initial Signal Clone data...")
    now = datetime.now(timezone.utc)

    # 1. Seed Users
    users_data = [
        {"id": 1, "phone": "+15550124836", "username": "demo.user", "display_name": "Demo User", "about": "Exploring Signal Clone!", "avatar_url": None, "is_online": True},
        {"id": 2, "phone": "+15550124837", "username": "maya.chen", "display_name": "Maya Chen", "about": "Coffee & code ☕", "avatar_url": None, "is_online": True},
        {"id": 3, "phone": "+15550124838", "username": "noah.williams", "display_name": "Noah Williams", "about": "Trail runner & tech enthusiast", "avatar_url": None, "is_online": False},
        {"id": 4, "phone": "+15550124839", "username": "sofia.rodriguez", "display_name": "Sofia Rodriguez", "about": "Designer & art lover 🎨", "avatar_url": None, "is_online": True},
        {"id": 5, "phone": "+15550124840", "username": "ava.thompson", "display_name": "Ava Thompson", "about": "Product lead @ TechCorp", "avatar_url": None, "is_online": False},
        {"id": 6, "phone": "+15550124841", "username": "daniel.kim", "display_name": "Daniel Kim", "about": "Building cool stuff", "avatar_url": None, "is_online": False},
        {"id": 7, "phone": "+15550124842", "username": "leila.hassan", "display_name": "Leila Hassan", "about": "Always curious ✨", "avatar_url": None, "is_online": False},
    ]

    users = []
    for u in users_data:
        user = User(
            id=u["id"],
            phone=u["phone"],
            username=u["username"],
            display_name=u["display_name"],
            about=u["about"],
            avatar_url=u["avatar_url"],
            is_online=u["is_online"],
            last_seen_at=now - timedelta(minutes=15 * u["id"]),
            created_at=now - timedelta(days=30)
        )
        db.add(user)
        users.append(user)
    db.commit()

    # 2. Seed Contacts for Demo User (id=1)
    contacts_ids = [2, 3, 4, 5, 6]
    for cid in contacts_ids:
        c = Contact(owner_id=1, contact_user_id=cid, created_at=now - timedelta(days=10))
        db.add(c)
        # Add reverse contacts so they see each other
        c_rev = Contact(owner_id=cid, contact_user_id=1, created_at=now - timedelta(days=10))
        db.add(c_rev)
    db.commit()

    # 3. Seed Conversations

    # 3a. Direct Chat: Demo User (1) & Maya Chen (2)
    conv_maya = Conversation(
        id=1, type="direct", direct_key="1_2", created_by=1,
        last_activity_at=now - timedelta(minutes=2), created_at=now - timedelta(days=5)
    )
    db.add(conv_maya)
    db.flush()
    db.add(ConversationMember(conversation_id=1, user_id=1, role="admin"))
    db.add(ConversationMember(conversation_id=1, user_id=2, role="admin"))

    # Messages for Maya chat
    maya_messages = [
        (2, "Hey! Are we still on for lunch today?", now - timedelta(minutes=30), "read"),
        (1, "Absolutely. How does 12:30 sound?", now - timedelta(minutes=25), "read"),
        (2, "Perfect. The little Italian place near the park?", now - timedelta(minutes=20), "read"),
        (1, "Yes! I booked us a table by the window.", now - timedelta(minutes=15), "read"),
        (2, "Perfect, see you then!", now - timedelta(minutes=2), "read"),
    ]

    last_msg_id = None
    for sender_id, text, timestamp, status in maya_messages:
        msg = Message(
            conversation_id=1, sender_id=sender_id, body=text, type="text",
            status=status, is_encrypted=False, created_at=timestamp
        )
        db.add(msg)
        db.flush()
        last_msg_id = msg.id
        # Receipts
        recipient_id = 2 if sender_id == 1 else 1
        db.add(MessageReceipt(message_id=msg.id, user_id=recipient_id, delivered_at=timestamp, read_at=timestamp))
        if sender_id == 1 and "booked" in text:
            db.add(Reaction(message_id=msg.id, user_id=2, emoji="♥"))
    
    conv_maya.last_message_id = last_msg_id

    # 3b. Group Chat: Weekend Hikers (Demo, Maya, Noah, Daniel)
    conv_hikers = Conversation(
        id=2, type="group", name="Weekend Hikers", avatar_url=None, created_by=3,
        last_activity_at=now - timedelta(hours=1), created_at=now - timedelta(days=7)
    )
    db.add(conv_hikers)
    db.flush()

    for uid, r in [(3, "admin"), (1, "member"), (2, "member"), (6, "member")]:
        db.add(ConversationMember(conversation_id=2, user_id=uid, role=r))

    hiker_msgs = [
        (None, "Noah Williams created the group", now - timedelta(days=2), "system"),
        (3, "Saturday looks clear. Shall we meet at the north trailhead?", now - timedelta(hours=2), "read"),
        (1, "Works for me. 8am?", now - timedelta(hours=1, minutes=45), "read"),
        (6, "I’ll bring extra water for everyone.", now - timedelta(hours=1), "read"),
    ]

    for sender_id, text, timestamp, status in hiker_msgs:
        mtype = "system" if sender_id is None else "text"
        msg = Message(
            conversation_id=2, sender_id=sender_id, body=text, type=mtype,
            status=status, is_encrypted=False, created_at=timestamp
        )
        db.add(msg)
        db.flush()
        conv_hikers.last_message_id = msg.id
        if sender_id:
            for uid in [1, 2, 3, 6]:
                if uid != sender_id:
                    db.add(MessageReceipt(message_id=msg.id, user_id=uid, delivered_at=timestamp, read_at=timestamp))

    # 3c. Direct Chat: Demo User (1) & Noah Williams (3)
    conv_noah = Conversation(
        id=3, type="direct", direct_key="1_3", created_by=1,
        last_activity_at=now - timedelta(days=1), created_at=now - timedelta(days=3)
    )
    db.add(conv_noah)
    db.flush()
    db.add(ConversationMember(conversation_id=3, user_id=1, role="admin"))
    db.add(ConversationMember(conversation_id=3, user_id=3, role="admin"))

    noah_msgs = [
        (1, "This view is unreal.", now - timedelta(days=1, hours=2), "read"),
        (3, "You made it! Send more photos when you can.", now - timedelta(days=1, hours=1), "read"),
    ]
    for sender_id, text, timestamp, status in noah_msgs:
        msg = Message(
            conversation_id=3, sender_id=sender_id, body=text, type="text",
            status=status, is_encrypted=False, created_at=timestamp
        )
        db.add(msg)
        db.flush()
        conv_noah.last_message_id = msg.id
        recipient_id = 3 if sender_id == 1 else 1
        db.add(MessageReceipt(message_id=msg.id, user_id=recipient_id, delivered_at=timestamp, read_at=timestamp))

    # 3d. Group Chat: Product team (Ava, Demo, Daniel, Leila)
    conv_prod = Conversation(
        id=4, type="group", name="Product team", avatar_url=None, created_by=5,
        last_activity_at=now - timedelta(days=1, hours=5), created_at=now - timedelta(days=10)
    )
    db.add(conv_prod)
    db.flush()
    for uid, r in [(5, "admin"), (1, "member"), (6, "member"), (7, "member")]:
        db.add(ConversationMember(conversation_id=4, user_id=uid, role=r, is_muted=(uid == 1)))

    prod_msgs = [
        (5, "I updated the project notes with today’s decisions.", now - timedelta(days=1, hours=6), "read"),
        (1, "Thanks, I’ll review them this evening.", now - timedelta(days=1, hours=5), "delivered"),
    ]
    for sender_id, text, timestamp, status in prod_msgs:
        msg = Message(
            conversation_id=4, sender_id=sender_id, body=text, type="text",
            status=status, is_encrypted=False, created_at=timestamp
        )
        db.add(msg)
        db.flush()
        conv_prod.last_message_id = msg.id

    # 3e. Direct Chat: Demo User (1) & Sofia Rodriguez (4)
    conv_sofia = Conversation(
        id=5, type="direct", direct_key="1_4", created_by=1,
        last_activity_at=now - timedelta(days=2), created_at=now - timedelta(days=4)
    )
    db.add(conv_sofia)
    db.flush()
    db.add(ConversationMember(conversation_id=5, user_id=1, role="admin"))
    db.add(ConversationMember(conversation_id=5, user_id=4, role="admin"))

    sofia_msgs = [
        (1, "We should try the new exhibit this weekend.", now - timedelta(days=2, hours=3), "read"),
        (4, "That sounds amazing!", now - timedelta(days=2, hours=2), "read"),
    ]
    for sender_id, text, timestamp, status in sofia_msgs:
        msg = Message(
            conversation_id=5, sender_id=sender_id, body=text, type="text",
            status=status, is_encrypted=False, created_at=timestamp
        )
        db.add(msg)
        db.flush()
        conv_sofia.last_message_id = msg.id

    # 3f. Note to Self: Demo User (1)
    conv_note = Conversation(
        id=6, type="note_to_self", name="Note to Self", direct_key="note_1", created_by=1,
        last_activity_at=now - timedelta(days=3), created_at=now - timedelta(days=20)
    )
    db.add(conv_note)
    db.flush()
    db.add(ConversationMember(conversation_id=6, user_id=1, role="admin"))

    note_msg = Message(
        conversation_id=6, sender_id=1, body="Passport renewal reminder — submit the form before Friday.",
        type="text", status="sent", is_encrypted=False, created_at=now - timedelta(days=3)
    )
    db.add(note_msg)
    db.flush()
    conv_note.last_message_id = note_msg.id

    db.commit()
    print("[SEED] Successfully seeded database!")
