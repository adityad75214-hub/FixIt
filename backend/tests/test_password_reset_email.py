import re
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.database import db_manager
from app.core.security import hash_token, verify_password
from app.services import notification_service


def _sync_db():
    return db_manager.db.sync_db


def test_password_reset_request_sends_link_and_stores_only_token_hash(
    client, monkeypatch
):
    sent = {}
    _sync_db().password_reset_tokens.delete_many({"user_id": "USR-TEST-STUDENT"})
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")
    monkeypatch.setattr(
        notification_service,
        "_send_email",
        lambda recipient, subject, body: sent.update(
            recipient=recipient, subject=subject, body=body
        ),
    )

    response = client.post(
        "/api/auth/password-reset/request",
        json={"email": "test.student@college.edu"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"].startswith("If an account exists")
    assert sent["recipient"] == "test.student@college.edu"
    assert sent["subject"] == "Reset your FixIt password"
    raw_token = re.search(r"token=([^\s]+)", sent["body"]).group(1)
    assert len(raw_token) >= 32

    stored = _sync_db().password_reset_tokens.find_one(
        {"user_id": "USR-TEST-STUDENT"}
    )
    assert stored is not None
    assert stored["_id"] == hash_token(raw_token)
    assert stored["_id"] != raw_token


def test_password_reset_email_failure_removes_unused_token(client, monkeypatch):
    _sync_db().password_reset_tokens.delete_many({"user_id": "USR-TEST-STUDENT"})
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")

    def fail_email(*args, **kwargs):
        raise RuntimeError("SMTP unavailable")

    monkeypatch.setattr(notification_service, "_send_email", fail_email)
    response = client.post(
        "/api/auth/password-reset/request",
        json={"email": "test.student@college.edu"},
    )

    assert response.status_code == 200
    assert response.json()["message"].startswith("If an account exists")
    assert _sync_db().password_reset_tokens.count_documents(
        {"user_id": "USR-TEST-STUDENT"}
    ) == 0


def test_password_reset_token_is_single_use_and_revokes_sessions(client):
    _sync_db().password_reset_tokens.delete_many({"user_id": "USR-TEST-STUDENT"})
    _sync_db().refresh_tokens.delete_many({"user_id": "USR-TEST-STUDENT"})
    raw_token = "test-reset-token-" + ("x" * 40)
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    sync_db = _sync_db()
    sync_db.password_reset_tokens.insert_one({
        "_id": token_hash,
        "user_id": "USR-TEST-STUDENT",
        "created_at": now,
        "expires_at": now + timedelta(minutes=15),
    })
    sync_db.refresh_tokens.insert_one({
        "user_id": "USR-TEST-STUDENT",
        "token_hash": "test-refresh-token-hash",
        "expires_at": now + timedelta(days=1),
    })

    response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "NewSecurePassword@123"},
    )

    assert response.status_code == 200, response.text
    user = sync_db.users.find_one({"_id": "USR-TEST-STUDENT"})
    assert verify_password("NewSecurePassword@123", user["password_hash"])
    assert user["token_version"] == 1
    assert sync_db.refresh_tokens.count_documents(
        {"user_id": "USR-TEST-STUDENT"}
    ) == 0
    assert sync_db.password_reset_tokens.count_documents(
        {"_id": token_hash}
    ) == 0

    replay = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "AnotherSecurePassword@123"},
    )
    assert replay.status_code == 400


def test_password_reset_rejects_expired_token(client):
    _sync_db().password_reset_tokens.delete_many({"user_id": "USR-TEST-STUDENT"})
    raw_token = "expired-reset-token-" + ("y" * 40)
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)
    _sync_db().password_reset_tokens.insert_one({
        "_id": token_hash,
        "user_id": "USR-TEST-STUDENT",
        "created_at": now - timedelta(hours=1),
        "expires_at": now - timedelta(seconds=1),
    })

    response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "NewSecurePassword@123"},
    )

    assert response.status_code == 400
    assert _sync_db().password_reset_tokens.find_one({"_id": token_hash}) is None
