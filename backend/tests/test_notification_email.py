import smtplib

import pytest

from app.core.config import settings
from app.services import notification_service


def test_send_email_uses_starttls_and_smtp_auth(monkeypatch):
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            calls.append(("close",))

        def ehlo(self):
            calls.append(("ehlo",))

        def starttls(self, context=None):
            calls.append(("starttls", context is not None))

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message):
            calls.append(("send", message["To"], message["From"], message["Subject"]))

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "smtp-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-secret")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.test")
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(notification_service.smtplib, "SMTP", FakeSMTP)

    notification_service._send_email(
        "student@example.test", "FixIt notice", "Test message"
    )

    assert ("connect", "smtp.test", 587, 15) in calls
    assert ("starttls", True) in calls
    assert ("login", "smtp-user", "smtp-secret") in calls
    assert ("send", "student@example.test", "noreply@example.test", "FixIt notice") in calls


def test_send_email_uses_implicit_tls_on_port_465(monkeypatch):
    calls = []

    class FakeSMTPSSL:
        def __init__(self, host, port, timeout, context=None):
            calls.append(("connect_ssl", host, port, timeout, context is not None))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def login(self, username, password):
            calls.append(("login", username, password))

        def send_message(self, message):
            calls.append(("send", message["To"]))

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.test")
    monkeypatch.setattr(settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(notification_service.smtplib, "SMTP_SSL", FakeSMTPSSL)

    notification_service._send_email("student@example.test", "Subject", "Body")

    assert calls[0][:4] == ("connect_ssl", "smtp.test", 465, 15)
    assert calls[0][4] is True
    assert ("send", "student@example.test") in calls


@pytest.mark.parametrize(
    "host,sender,username,password,recipient",
    [
        (None, "noreply@example.test", None, None, "student@example.test"),
        ("smtp.test", None, None, None, "student@example.test"),
        ("smtp.test", "noreply@example.test", "smtp-user", None, "student@example.test"),
        ("smtp.test", "noreply@example.test", None, None, ""),
    ],
)
def test_send_email_rejects_incomplete_configuration(
    monkeypatch, host, sender, username, password, recipient
):
    monkeypatch.setattr(settings, "SMTP_HOST", host)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", sender)
    monkeypatch.setattr(settings, "SMTP_USERNAME", username)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", password)

    with pytest.raises((RuntimeError, ValueError)):
        notification_service._send_email(recipient, "Subject", "Body")


def test_send_email_refuses_plaintext_smtp(monkeypatch):
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@example.test")
    monkeypatch.setattr(settings, "SMTP_STARTTLS", False)

    with pytest.raises(RuntimeError, match="must use STARTTLS or implicit TLS"):
        notification_service._send_email("student@example.test", "Subject", "Body")
