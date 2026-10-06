def test_direct_chat_and_messages(client):
    # Register user1
    r1 = client.post("/api/v1/auth/verify-otp", json={"identifier": "+15550124836", "otp": "123456"})
    token1 = r1.json()["access_token"]
    user1_id = r1.json()["user"]["id"]
    h1 = {"Authorization": f"Bearer {token1}"}

    # Register user2
    r2 = client.post("/api/v1/auth/verify-otp", json={"identifier": "+15550124837", "otp": "123456"})
    token2 = r2.json()["access_token"]
    user2_id = r2.json()["user"]["id"]
    h2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates direct conversation with User 2
    conv_resp = client.post("/api/v1/conversations", json={"user_id": user2_id}, headers=h1)
    assert conv_resp.status_code == 200
    conv_id = conv_resp.json()["id"]

    # User 1 sends message
    msg_resp = client.post(f"/api/v1/conversations/{conv_id}/messages", json={"body": "Hello World", "client_id": "c1"}, headers=h1)
    assert msg_resp.status_code == 200
    assert msg_resp.json()["body"] == "Hello World"
    msg_id = msg_resp.json()["id"]

    # User 2 lists conversations -> sees unread message
    list_resp = client.get("/api/v1/conversations", headers=h2)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["unread_count"] == 1

    # User 2 marks as read
    read_resp = client.post(f"/api/v1/conversations/{conv_id}/read?up_to_message_id={msg_id}", headers=h2)
    assert read_resp.status_code == 200

    # User 2 lists conversations again -> unread_count is 0
    list_resp2 = client.get("/api/v1/conversations", headers=h2)
    assert list_resp2.json()[0]["unread_count"] == 0

def test_note_to_self(client):
    r1 = client.post("/api/v1/auth/verify-otp", json={"identifier": "self_user", "otp": "123456"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}

    note_resp = client.post("/api/v1/conversations/note-to-self", headers=h1)
    assert note_resp.status_code == 200
    assert note_resp.json()["type"] == "note_to_self"
