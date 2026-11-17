import uuid

from app.core.config import settings
from app.core.database import db_manager
from app.core.security import create_access_token


def _setup_institution(primary_id="USR-TEST-ADMIN"):
    institution_id = f"INST-GOV-{uuid.uuid4().hex[:8].upper()}"
    db = db_manager.db.sync_db
    db.institutions.insert_one({
        "_id": institution_id, "name": "Governance Test College",
        "slug": f"gov-{uuid.uuid4().hex[:6]}", "email_domains": ["gov-test.edu"],
        "status": "active",
    })
    db.users.update_one(
        {"_id": primary_id},
        {"$set": {"institution_id": institution_id, "admin_level": "primary", "is_active": True}},
    )
    return institution_id


def test_college_admin_request_requires_primary_approval(client, admin_token, monkeypatch):
    import app.services.notification_service as mailer

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    sent = {}
    monkeypatch.setattr(mailer, "_send_email", lambda recipient, subject, body: sent.update(recipient=recipient, body=body))

    institution_id = _setup_institution()
    requester_id = f"USR-REQUESTER-{uuid.uuid4().hex[:8]}"
    db = db_manager.db.sync_db
    db.users.insert_one({
        "_id": requester_id, "email": f"requester-{uuid.uuid4().hex[:6]}@gov-test.edu",
        "name": "College Admin", "role": "admin", "admin_level": "college",
        "institution_id": institution_id, "is_active": True, "token_version": 0,
    })
    requester_token = create_access_token({"sub": requester_id, "role": "admin", "ver": 0})

    response = client.post(
        f"/api/institutions/{institution_id}/admin-requests",
        headers={"Authorization": f"Bearer {requester_token}"},
        json={"name": "New Admin", "email": f"new-{uuid.uuid4().hex[:6]}@gov-test.edu", "designation": "HOD", "department": "CSE"},
    )
    assert response.status_code == 202, response.text
    request_id = response.json()["request_id"]
    assert db.notifications.find_one({"user_id": "USR-TEST-ADMIN", "title": "Administrator approval requested"})

    denied = client.get(
        f"/api/institutions/{institution_id}/admin-requests",
        headers={"Authorization": f"Bearer {requester_token}"},
    )
    assert denied.status_code == 403

    approved = client.post(
        f"/api/institutions/{institution_id}/admin-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approved.status_code == 200, approved.text
    assert sent["recipient"].endswith("@gov-test.edu")
    assert db.admin_requests.find_one({"_id": request_id})["status"] == "approved"
    assert db.notifications.find_one({"user_id": requester_id, "title": "Administrator request approved"})
    invitation = db.admin_invitations.find_one({"email": sent["recipient"]})
    assert invitation["admin_level"] == "college"


def test_college_admin_cannot_directly_invite_without_primary_role(client, monkeypatch):
    institution_id = _setup_institution()
    requester_id = f"USR-NONPRIMARY-{uuid.uuid4().hex[:8]}"
    db = db_manager.db.sync_db
    db.users.insert_one({
        "_id": requester_id, "email": f"nonprimary-{uuid.uuid4().hex[:6]}@gov-test.edu",
        "name": "College Admin", "role": "admin", "admin_level": "college",
        "institution_id": institution_id, "is_active": True, "token_version": 0,
    })
    token = create_access_token({"sub": requester_id, "role": "admin", "ver": 0})
    response = client.post(
        f"/api/institutions/{institution_id}/admins/invitations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Another Admin", "email": f"another-{uuid.uuid4().hex[:6]}@gov-test.edu"},
    )
    assert response.status_code == 403


def test_admin_cannot_create_admin_through_user_management(client, admin_token):
    response = client.post(
        "/api/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Bypass Admin", "email": f"bypass-{uuid.uuid4().hex[:6]}@college.edu",
            "password": "SecurePassphrase123!", "role": "admin",
            "department": "Administration",
        },
    )
    assert response.status_code == 403

def test_platform_invitation_assigns_first_primary_admin(client, monkeypatch):
    import app.services.notification_service as mailer

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    sent = {}
    monkeypatch.setattr(mailer, "_send_email", lambda recipient, subject, body: sent.update(recipient=recipient, body=body))

    institution_id = f"INST-FIRST-{uuid.uuid4().hex[:8].upper()}"
    db = db_manager.db.sync_db
    db.institutions.insert_one({
        "_id": institution_id, "name": "First Admin College",
        "slug": f"first-{uuid.uuid4().hex[:6]}", "email_domains": ["first-test.edu"],
        "status": "active",
    })
    platform_id = f"USR-PLATFORM-{uuid.uuid4().hex[:8]}"
    db.users.insert_one({
        "_id": platform_id, "email": f"platform-{uuid.uuid4().hex[:6]}@fixit.test",
        "name": "Platform Operator", "role": "platform_admin",
        "is_active": True, "token_version": 0,
    })
    platform_token = create_access_token({"sub": platform_id, "role": "platform_admin", "ver": 0})
    email = f"primary-{uuid.uuid4().hex[:6]}@first-test.edu"

    response = client.post(
        f"/api/institutions/{institution_id}/admins/invitations",
        headers={"Authorization": f"Bearer {platform_token}"},
        json={"name": "First College Admin", "email": email},
    )
    assert response.status_code == 202, response.text
    invitation = db.admin_invitations.find_one({"email": email})
    assert invitation["admin_level"] == "primary"
    assert sent["recipient"] == email
