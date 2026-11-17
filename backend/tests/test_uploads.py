from app.api.uploads import _detect_file_type
from app.models.comment import CommentCreate


def test_upload_detects_jpeg_signature():
    assert _detect_file_type(b"\xff\xd8\xff\xe0sample") == "image/jpeg"


def test_upload_detects_png_signature():
    assert _detect_file_type(b"\x89PNG\r\n\x1a\nrest") == "image/png"


def test_upload_detects_pdf_signature():
    assert _detect_file_type(b"%PDF-1.7 sample") == "application/pdf"


def test_upload_rejects_unknown_binary_content():
    assert _detect_file_type(b"\x00\x01\x02\x03") is None


def test_comment_accepts_internal_upload_reference():
    comment = CommentCreate(
        content="Screenshot attached",
        attachments=["/api/uploads/0123456789abcdef0123456789abcdef"],
    )
    assert comment.attachments == ["/api/uploads/0123456789abcdef0123456789abcdef"]


def test_comment_rejects_malformed_internal_upload_reference():
    from pydantic import ValidationError
    import pytest

    with pytest.raises(ValidationError):
        CommentCreate(content="Invalid", attachments=["/api/uploads/not-a-valid-id"])
