import re
import uuid

from app.core.config import settings
from app.core.database import db_manager


def _institution():
    institution_id = f"INST-OTP-{uuid.uuid4().hex[:8].upper()}"
    slug = f"otp-college-{uuid.uuid4().hex[:6]}"
    db_manager.db.sync_db.institutions.insert_one({
        "_id": institution_id,
        "name": "OTP Test College",
        "slug": slug,
        "email_domains": ["otp-test.edu"],
        "status": "active",
    })
    return institution_id, slug


def test_registration_requires_approved_college_domain(client, monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_REGISTRATION_ENABLED", True)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    _, slug = _institution()

    response = client.post("/api/auth/registration/request-code", json={
        "institution_slug": slug,
        "name": "Wrong Domain",
        "email": "someone@gmail.com",
        "role": "student",
        "department": "Computer Science",
        "identifier": "USN-001",
    })
    assert response.status_code == 403


def test_student_can_register_after_college_email_otp(client, monkeypatch):
    import app.services.notification_service as mailer

    monkeypatch.setattr(settings, "PUBLIC_REGISTRATION_ENABLED", True)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    _, slug = _institution()
    sent = {}

    def fake_send_email(recipient, subject, body):
        sent.update(recipient=recipient, subject=subject, body=body)

    monkeypatch.setattr(mailer, "_send_email", fake_send_email)
    email = f"student-{uuid.uuid4().hex[:8]}@otp-test.edu"
    payload = {
        "institution_slug": slug,
        "name": "Verified Student",
        "email": email,
        "role": "student",
        "department": "Computer Science",
        "identifier": "USN-OTP-001",
    }

    requested = client.post("/api/auth/registration/request-code", json=payload)
    assert requested.status_code == 202, requested.text
    assert db_manager.db.sync_db.users.find_one({"email": email}) is None
    code = re.search(r"verification code .* is: (\d{6})", sent["body"], re.IGNORECASE).group(1)

    verified = client.post("/api/auth/registration/verify-code", json={"email": email, "code": code, "password": "SecurePassphrase123!"})
    assert verified.status_code == 201, verified.text
    assert verified.json()["user"]["role"] == "student"
    assert verified.json()["user"]["institution_id"].startswith("INST-OTP-")
    stored = db_manager.db.sync_db.users.find_one({"email": email})
    assert stored["email_verified"] is True
    assert stored["approval_method"] == "institution_email_otp"
    assert db_manager.db.sync_db.pending_registrations.find_one({"email": email}) is None


def test_faculty_can_register_after_college_email_otp(client, monkeypatch):
    import app.services.notification_service as mailer

    monkeypatch.setattr(settings, "PUBLIC_REGISTRATION_ENABLED", True)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    _, slug = _institution()
    sent = {}
    monkeypatch.setattr(mailer, "_send_email", lambda recipient, subject, body: sent.update(body=body))
    email = f"faculty-{uuid.uuid4().hex[:8]}@otp-test.edu"

    requested = client.post("/api/auth/registration/request-code", json={
        "institution_slug": slug,
        "name": "Verified Faculty",
        "email": email,
        "role": "faculty",
        "department": "Computer Science",
        "identifier": "EMP-OTP-001",
    })
    assert requested.status_code == 202, requested.text
    code = re.search(r"verification code .* is: (\d{6})", sent["body"], re.IGNORECASE).group(1)

    verified = client.post("/api/auth/registration/verify-code", json={"email": email, "code": code, "password": "SecurePassphrase123!"})
    assert verified.status_code == 201, verified.text
    assert verified.json()["user"]["role"] == "faculty"


def test_incorrect_registration_code_does_not_create_user(client, monkeypatch):
    import app.services.notification_service as mailer

    monkeypatch.setattr(settings, "PUBLIC_REGISTRATION_ENABLED", True)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.test")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.test")
    _, slug = _institution()
    monkeypatch.setattr(mailer, "_send_email", lambda *args: None)
    email = f"wrong-code-{uuid.uuid4().hex[:8]}@otp-test.edu"

    requested = client.post("/api/auth/registration/request-code", json={
        "institution_slug": slug,
        "name": "Pending User",
        "email": email,
        "password": "SecurePassphrase123!",
        "role": "student",
        "department": "Computer Science",
        "identifier": "USN-OTP-002",
    })
    assert requested.status_code == 202, requested.text
    verified = client.post("/api/auth/registration/verify-code", json={"email": email, "code": "000000", "password": "SecurePassphrase123!"})
    assert verified.status_code == 400
    assert db_manager.db.sync_db.users.find_one({"email": email}) is None
