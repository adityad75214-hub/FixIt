import re
import uuid

from app.core.config import settings
from app.core.database import db_manager
from app.core.security import create_access_token


def test_platform_admin_invites_college_admin_and_invitation_is_single_use(client, monkeypatch):
    sync_db = db_manager.db.sync_db
    suffix = uuid.uuid4().hex[:8]
    institution_id = f"INST-INV-{suffix.upper()}"
    email = f"admin-{suffix}@invite-college.edu"
    sync_db.institutions.insert_one({
        "_id": institution_id,
        "name": "Invitation Test College",
        "slug": f"invite-college-{suffix}",
        "email_domains": ["invite-college.edu"],
        "status": "active",
    })
    platform_admin_id = f"USR-PLATFORM-{suffix.upper()}"
    sync_db.users.insert_one({
        "_id": platform_admin_id,
        "email": f"platform-{suffix}@fixit.example",
        "name": "Test Platform Admin",
        "role": "platform_admin",
        "is_active": True,
        "token_version": 0,
    })
    token = create_access_token({"sub": platform_admin_id, "role": "platform_admin", "ver": 0})
    sent = {}

    def fake_send_email(recipient, subject, body):
        sent.update(recipient=recipient, subject=subject, body=body)

    monkeypatch.setattr("app.services.notification_service._send_email", fake_send_email)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.example")
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")

    invited = client.post(
        f"/api/institutions/{institution_id}/admins/invitations",
        headers={"Authorization": f"Bearer {token}"},
        json={"email": email, "name": "College Admin"},
    )
    assert invited.status_code == 202, invited.text
    assert sent["recipient"] == email
    assert sync_db.users.find_one({"email": email}) is None

    raw_token = re.search(r"token=([^\s]+)", sent["body"]).group(1)
    accepted = client.post(
        "/api/institutions/admin-invitations/accept",
        json={"token": raw_token, "password": "A-Strong-Password-123!"},
    )
    assert accepted.status_code == 201, accepted.text
    created = sync_db.users.find_one({"email": email})
    assert created["role"] == "admin"
    assert created["institution_id"] == institution_id

    replay = client.post(
        "/api/institutions/admin-invitations/accept",
        json={"token": raw_token, "password": "Another-Strong-Password-123!"},
    )
    assert replay.status_code == 400


def test_primary_admin_can_list_resend_and_cancel_pending_invitation(client, monkeypatch):
    sync_db = db_manager.db.sync_db
    suffix = uuid.uuid4().hex[:8]
    institution_id = f"INST-GOV-{suffix.upper()}"
    email = f"admin-{suffix}@governance-college.edu"
    sync_db.institutions.insert_one({
        "_id": institution_id, "name": "Governance Test College",
        "slug": f"governance-{suffix}", "email_domains": ["governance-college.edu"],
        "status": "active",
    })
    admin_id = f"USR-PRIMARY-{suffix.upper()}"
    sync_db.users.insert_one({
        "_id": admin_id, "email": f"primary-{suffix}@governance-college.edu",
        "name": "Primary Admin", "role": "admin", "admin_level": "primary",
        "institution_id": institution_id, "is_active": True, "token_version": 0,
    })
    token = create_access_token({"sub": admin_id, "role": "admin", "ver": 0})
    sent = []
    monkeypatch.setattr(
        "app.services.notification_service._send_email",
        lambda recipient, subject, body: sent.append({"recipient": recipient, "body": body}),
    )
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.example")
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        f"/api/institutions/{institution_id}/admins/invitations",
        headers=headers, json={"email": email, "name": "Invited Admin"},
    )
    assert created.status_code == 202, created.text
    invitation_id = sync_db.admin_invitations.find_one({"email": email})["_id"]
    first_token = re.search(r"token=([^\s]+)", sent[-1]["body"]).group(1)

    listed = client.get(f"/api/institutions/{institution_id}/admin-invitations", headers=headers)
    assert listed.status_code == 200, listed.text
    assert [row["id"] for row in listed.json()] == [invitation_id]
    assert "token_hash" not in listed.text

    resent = client.post(
        f"/api/institutions/{institution_id}/admin-invitations/{invitation_id}/resend",
        headers=headers,
    )
    assert resent.status_code == 200, resent.text
    second_token = re.search(r"token=([^\s]+)", sent[-1]["body"]).group(1)
    assert first_token != second_token
    old_link = client.post("/api/institutions/admin-invitations/accept", json={
        "token": first_token, "password": "A-Strong-Password-123!",
    })
    assert old_link.status_code == 400

    cancelled = client.delete(
        f"/api/institutions/{institution_id}/admin-invitations/{invitation_id}",
        headers=headers,
    )
    assert cancelled.status_code == 200, cancelled.text
    new_link = client.post("/api/institutions/admin-invitations/accept", json={
        "token": second_token, "password": "A-Strong-Password-123!",
    })
    assert new_link.status_code == 400
    assert sync_db.users.find_one({"email": email}) is None


def test_admin_invitation_acceptance_rejects_pending_student_registration(client, monkeypatch):
    from datetime import datetime, timedelta, timezone

    sync_db = db_manager.db.sync_db
    suffix = uuid.uuid4().hex[:8]
    institution_id = f"INST-CROSS-{suffix.upper()}"
    email = f"cross-role-{suffix}@cross-college.edu"
    sync_db.institutions.insert_one({
        "_id": institution_id, "name": "Cross Role Test College",
        "slug": f"cross-{suffix}", "email_domains": ["cross-college.edu"],
        "status": "active",
    })
    sent = {}
    monkeypatch.setattr(
        "app.services.notification_service._send_email",
        lambda recipient, subject, body: sent.update(body=body),
    )
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.example")
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")

    invited = client.post(
        f"/api/institutions/{institution_id}/admins/invitations",
        headers={"Authorization": f"Bearer {create_access_token({'sub': 'platform-test', 'role': 'platform_admin', 'ver': 0})}"},
        json={"email": email, "name": "Cross Role Admin"},
    )
    # A valid platform-admin principal is supplied by the shared test fixture.
    assert invited.status_code == 202, invited.text
    raw_token = re.search(r"token=([^\s]+)", sent["body"]).group(1)
    sync_db.pending_registrations.insert_one({
        "_id": f"REG-{suffix.upper()}", "email": email,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
    })
    accepted = client.post("/api/institutions/admin-invitations/accept", json={
        "token": raw_token, "password": "A-Strong-Password-123!",
    })
    assert accepted.status_code == 409
    assert sync_db.users.find_one({"email": email}) is None
