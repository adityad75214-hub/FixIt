def test_student_registration_success(client):
    res = client.post("/api/auth/register", json={
        "email": "new.student@college.edu",
        "password": "Password123!",
        "name": "New Student",
        "role": "student",
        "department": "Physics",
        "phone": "+1 555-1234"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new.student@college.edu"
    assert data["user"]["role"] == "student"
    assert "fixit_refresh_token" in res.cookies

def test_prevent_public_admin_registration(client):
    res = client.post("/api/auth/register", json={
        "email": "rogue.admin@college.edu",
        "password": "Password123!",
        "name": "Rogue Admin",
        "role": "admin"
    })
    assert res.status_code == 403
    assert "Only student accounts" in res.json()["detail"]

def test_prevent_public_staff_registration(client):
    res = client.post("/api/auth/register", json={
        "email": "rogue.staff@college.edu",
        "password": "Password123!",
        "name": "Rogue Staff",
        "role": "staff"
    })
    assert res.status_code == 403
    assert "Only student accounts" in res.json()["detail"]

def test_login_success(client):
    res = client.post("/api/auth/login", json={
        "email": "test.admin@college.edu",
        "password": "TestAdmin@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test.admin@college.edu"
    assert "fixit_refresh_token" in res.cookies

def test_login_invalid_credentials(client):
    res = client.post("/api/auth/login", json={
        "email": "test.admin@college.edu",
        "password": "WrongPassword"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_refresh_token_rotation(client):
    # Log in first to acquire refresh cookie
    login_res = client.post("/api/auth/login", json={
        "email": "test.student@college.edu",
        "password": "TestStudent@123"
    })
    assert login_res.status_code == 200
    refresh_cookie = login_res.cookies.get("fixit_refresh_token")
    assert refresh_cookie is not None

    # Call /refresh with cookie
    refresh_res = client.post("/api/auth/refresh", cookies={"fixit_refresh_token": refresh_cookie})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    assert refresh_data["user"]["email"] == "test.student@college.edu"

    # Verify cookie has been rotated to a new token
    new_refresh_cookie = refresh_res.cookies.get("fixit_refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_cookie

def test_get_current_user_profile(client, student_token):
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test.student@college.edu"
    assert data["role"] == "student"
    assert "password_hash" not in data  # Never expose password hashes


def test_refresh_token_cannot_be_reused(client):
    login_res = client.post("/api/auth/login", json={
        "email": "test.student@college.edu",
        "password": "TestStudent@123"
    })
    assert login_res.status_code == 200
    old_refresh = login_res.cookies.get("fixit_refresh_token")
    assert old_refresh

    first_refresh = client.post("/api/auth/refresh", cookies={"fixit_refresh_token": old_refresh})
    assert first_refresh.status_code == 200

    replay = client.post("/api/auth/refresh", cookies={"fixit_refresh_token": old_refresh})
    assert replay.status_code == 401


def test_prevent_public_faculty_registration(client):
    res = client.post("/api/auth/register", json={
        "email": "unverified.faculty@college.edu",
        "password": "Password123!",
        "name": "Unverified Faculty",
        "role": "faculty"
    })
    assert res.status_code == 403
    assert "Only student accounts" in res.json()["detail"]


def test_password_change_revokes_existing_access_and_refresh_tokens(client):
    login_res = client.post("/api/auth/login", json={
        "email": "test.student@college.edu",
        "password": "TestStudent@123"
    })
    assert login_res.status_code == 200
    old_access = login_res.json()["access_token"]
    old_refresh = login_res.cookies.get("fixit_refresh_token")

    changed = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {old_access}"},
        json={"current_password": "TestStudent@123", "new_password": "NewSecurePassphrase123!"}
    )
    assert changed.status_code == 200

    old_access_check = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_access}"})
    assert old_access_check.status_code == 401

    old_refresh_check = client.post("/api/auth/refresh", cookies={"fixit_refresh_token": old_refresh})
    assert old_refresh_check.status_code == 401

    new_login = client.post("/api/auth/login", json={
        "email": "test.student@college.edu",
        "password": "NewSecurePassphrase123!"
    })
    assert new_login.status_code == 200


def test_login_rate_limit_counts_only_failed_attempts():
    import asyncio
    import uuid
    import pytest
    from fastapi import HTTPException
    from app.api.auth import check_login_rate_limit, record_login_failure
    from app.core.database import db_manager

    async def scenario():
        key = f"test-rate-limit:{uuid.uuid4().hex}"
        db = db_manager.db

        # Merely checking the limit must not consume an attempt.
        await check_login_rate_limit(db, key, max_attempts=2, window_seconds=60)
        await check_login_rate_limit(db, key, max_attempts=2, window_seconds=60)
        assert (await db.login_rate_limits.find_one({"_id": key}))["attempts"] == 0

        await record_login_failure(db, key, max_attempts=2, window_seconds=60)
        await check_login_rate_limit(db, key, max_attempts=2, window_seconds=60)
        await record_login_failure(db, key, max_attempts=2, window_seconds=60)

        with pytest.raises(HTTPException) as error:
            await check_login_rate_limit(db, key, max_attempts=2, window_seconds=60)
        assert error.value.status_code == 429

    asyncio.run(scenario())


def test_logout_revokes_access_and_refresh_tokens(client):
    login_res = client.post("/api/auth/login", json={
        "email": "test.student@college.edu",
        "password": "TestStudent@123"
    })
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]
    refresh_token = login_res.cookies.get("fixit_refresh_token")
    assert refresh_token

    logout_res = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        cookies={"fixit_refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200, logout_res.text

    access_check = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert access_check.status_code == 401

    refresh_check = client.post(
        "/api/auth/refresh",
        cookies={"fixit_refresh_token": refresh_token},
    )
    assert refresh_check.status_code == 401
