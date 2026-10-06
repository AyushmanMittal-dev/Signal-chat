def test_unauthorized_access(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 403 or response.status_code == 401

def test_cross_user_group_admin_forbidden(client):
    # Register User 1
    r1 = client.post("/api/v1/auth/verify-otp", json={"identifier": "user1", "otp": "123456"})
    token1 = r1.json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # Register User 2
    r2 = client.post("/api/v1/auth/verify-otp", json={"identifier": "user2", "otp": "123456"})
    token2 = r2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 creates group
    group_resp = client.post("/api/v1/groups", json={"name": "User1 Group", "member_ids": []}, headers=headers1)
    assert group_resp.status_code == 200
    group_id = group_resp.json()["id"]

    # User 2 attempts to add member to User 1's group -> should fail with 403
    add_resp = client.post(f"/api/v1/groups/{group_id}/members", json={"user_ids": [2]}, headers=headers2)
    assert add_resp.status_code == 403
