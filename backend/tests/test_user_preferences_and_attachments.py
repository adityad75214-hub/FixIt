import pytest
from pydantic import ValidationError

from app.models.comment import CommentCreate
from app.models.user import UserPreferences


def test_user_preferences_default_to_enabled_notifications_and_english():
    preferences = UserPreferences()
    assert preferences.email_notifications is True
    assert preferences.in_app_notifications is True
    assert preferences.language == "en"


def test_user_preferences_accept_hindi_and_notification_opt_out():
    preferences = UserPreferences(
        email_notifications=False,
        in_app_notifications=False,
        language="hi",
    )
    assert preferences.language == "hi"
    assert preferences.email_notifications is False
    assert preferences.in_app_notifications is False


def test_user_preferences_reject_unsupported_language():
    with pytest.raises(ValidationError):
        UserPreferences(language="fr")


def test_ticket_comment_accepts_secure_attachment_links():
    comment = CommentCreate(
        content="Please see the attached screenshot.",
        attachments=["https://files.example.org/screenshot.png"],
    )
    assert len(comment.attachments) == 1


def test_ticket_comment_rejects_non_https_attachment_links():
    with pytest.raises(ValidationError):
        CommentCreate(
            content="Unsafe attachment",
            attachments=["http://files.example.org/screenshot.png"],
        )


def test_ticket_comment_limits_attachment_count():
    with pytest.raises(ValidationError):
        CommentCreate(
            content="Too many attachments",
            attachments=[f"https://files.example.org/{i}.png" for i in range(6)],
        )
