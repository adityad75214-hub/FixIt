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

    raw_token = re.search(r"token=([^\\s]+)", sent["body"]).group(1)
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
