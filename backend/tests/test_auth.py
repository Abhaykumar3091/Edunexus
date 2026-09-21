import pytest
from httpx import AsyncClient
from app.core.security import get_password_hash, verify_password


def test_argon2id_hashing():
    """
    Verify Argon2id password hashing and verification functionality.
    """
    raw_password = "SuperSecretPassword123!"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


@pytest.mark.asyncio
async def test_register_student(client: AsyncClient):
    """
    Test registering a new student account.
    """
    payload = {
        "email": "new.student@university.edu",
        "password": "SecurePassword123!",
        "full_name": "Jordan Smith",
        "role": "STUDENT",
        "university_id": "STU99001",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "new.student@university.edu"
    assert data["data"]["role"] == "STUDENT"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, student_user):
    """
    Test that duplicate registration with an existing email is rejected.
    """
    payload = {
        "email": student_user.email,
        "password": "AnotherPassword123!",
        "full_name": "Another Name",
        "role": "STUDENT",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "BAD_REQUEST"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, student_user):
    """
    Test successful login with Argon2id verified credentials.
    """
    login_payload = {
        "email": student_user.email,
        "password": "TestPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    token_info = data["data"]
    assert "access_token" in token_info
    assert token_info["token_type"] == "bearer"
    assert token_info["role"] == "STUDENT"
    assert token_info["email"] == student_user.email


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, student_user):
    """
    Test login fails with incorrect password.
    """
    login_payload = {
        "email": student_user.email,
        "password": "IncorrectPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient, student_user):
    """
    Test fetching authenticated user profile using Bearer JWT.
    """
    login_res = await client.post("/api/v1/auth/login", json={
        "email": student_user.email,
        "password": "TestPassword123!",
    })
    token = login_res.json()["data"]["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == student_user.email
    assert data["data"]["role"] == "STUDENT"


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """
    Test that calling protected endpoint without token returns 401.
    """
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
