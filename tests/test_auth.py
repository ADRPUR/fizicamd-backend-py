import uuid


def test_register_and_login(client):
    email = f"test_{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": "StrongPass123",
        "confirmPassword": "StrongPass123",
        "firstName": "Test",
        "lastName": "User",
    }
    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 200

    login = client.post("/api/auth/login", json={"email": email, "password": "StrongPass123"})
    assert login.status_code == 200
    data = login.json()
    assert "accessToken" in data
    assert data["user"]["email"] == email
