def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_request_otp(client):
    response = client.post("/api/v1/auth/request-otp", json={"phone": "+15550124836"})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_verify_otp_fixed_code(client):
    # Verify OTP 123456
    response = client.post("/api/v1/auth/verify-otp", json={"identifier": "+15550124836", "otp": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["phone"] == "+15550124836"

def test_verify_otp_invalid_code(client):
    response = client.post("/api/v1/auth/verify-otp", json={"identifier": "+15550124836", "otp": "999999"})
    assert response.status_code == 400
