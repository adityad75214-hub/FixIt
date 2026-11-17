import re
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.database import get_database
from app.core.security import get_current_user

router = APIRouter(prefix="/uploads", tags=["File Uploads"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
}


def _detect_file_type(data: bytes):
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data and b"\x00" not in data:
        try:
            data.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            pass
    return None


def _can_access_profile_upload(document: dict, user: dict) -> bool:
    return document.get("user_id") == user.get("id") or user.get("role") == "admin"


async def _ticket_for_user(db, ticket_id: str, user: dict, *, for_upload: bool):
    ticket = await db.tickets.find_one({"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    role = user.get("role")
    if role in ("student", "faculty"):
        allowed = ticket.get("created_by", {}).get("id") == user.get("id")
    elif role == "staff":
        assigned_id = (ticket.get("assigned_to") or {}).get("id")
        allowed = assigned_id == user.get("id") if for_upload else assigned_id in (None, user.get("id"))
    else:
        allowed = role == "admin"
    if not allowed:
        raise HTTPException(status_code=403, detail="You do not have access to this ticket's attachments.")
    return ticket


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = Query(..., pattern="^(profile|ticket)$"),
    ticket_id: str | None = Query(default=None, max_length=80),
    current_user: dict = Depends(get_current_user),
):
    if purpose == "ticket" and not ticket_id:
        raise HTTPException(status_code=400, detail="ticket_id is required for ticket attachments.")
    if purpose == "profile" and ticket_id:
        raise HTTPException(status_code=400, detail="Profile uploads cannot be linked to a ticket.")

    db = get_database()
    ticket = await _ticket_for_user(db, ticket_id, current_user, for_upload=True) if ticket_id else None

    chunks = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="Files must be 5 MB or smaller.")
        chunks.append(chunk)
    data = b"".join(chunks)
    detected_type = _detect_file_type(data)
    if not detected_type or detected_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Allowed files: JPG, PNG, WEBP, GIF, PDF, and TXT.")
    if purpose == "profile" and not detected_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Profile pictures must be JPG, PNG, WEBP, or GIF images.")

    upload_id = uuid.uuid4().hex
    original_name = Path(file.filename or "upload").name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", original_name)[:120] or "upload"
    document = {
        "_id": upload_id,
        "user_id": current_user["id"],
        "purpose": purpose,
        "ticket_id": ticket.get("ticket_id") if ticket else None,
        "filename": safe_name,
        "content_type": detected_type,
        "size": total,
        "data": data,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.uploads.insert_one(document)
    return {
        "id": upload_id,
        "filename": safe_name,
        "content_type": detected_type,
        "size": total,
        "url": f"/api/uploads/{upload_id}",
    }


@router.get("/{upload_id}")
async def download_file(
    upload_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    document = await db.uploads.find_one({"_id": upload_id})
    if not document:
        raise HTTPException(status_code=404, detail="File not found")

    if document.get("purpose") == "ticket":
        await _ticket_for_user(db, document.get("ticket_id", ""), current_user, for_upload=False)
    elif document.get("purpose") == "profile":
        if not _can_access_profile_upload(document, current_user):
            raise HTTPException(status_code=404, detail="File not found")
    else:
        raise HTTPException(status_code=404, detail="File not found")

    content_type = document.get("content_type", "application/octet-stream")
    filename = document.get("filename", "download")
    disposition = "inline" if content_type.startswith("image/") else "attachment"
    return StreamingResponse(
        BytesIO(document["data"]),
        media_type=content_type,
        headers={
            "Content-Length": str(document.get("size", len(document["data"]))),
            "Content-Disposition": f"{disposition}; filename=\"{filename}\"",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
