import uuid
from datetime import datetime, timezone

from app.core.database import db_manager


def _insert_notification(user_id, institution_id, *, is_read=False):
    notification_id = f"NOTIF-TEST-{uuid.uuid4().hex[:12]}"
    db_manager.db.sync_db.notifications.insert_one({
        "_id": notification_id,
        "user_id": user_id,
        "institution_id": institution_id,
        "title": "Test notification",
        "message": "Notification body",
        "link": "/tickets",
        "type": "ticket_update",
        "is_read": is_read,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return notification_id


def test_student_receives_only_own_tenant_notifications(client, student_token):
    own_id = _insert_notification("USR-TEST-STUDENT", "INST-DEFAULT")
    _insert_notification("USR-OTHER-STUDENT", "INST-DEFAULT")
    _insert_notification("USR-TEST-STUDENT", "INST-OTHER")

    response = client.get(
        "/api/notifications",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["unread_count"] == 1
    assert [item["id"] for item in data["notifications"]] == [own_id]
    assert data["notifications"][0]["user_id"] == "USR-TEST-STUDENT"


def test_student_can_mark_only_own_notification_read(client, student_token):
    own_id = _insert_notification("USR-TEST-STUDENT", "INST-DEFAULT")
    other_id = _insert_notification("USR-OTHER-STUDENT", "INST-DEFAULT")

    response = client.put(
        f"/api/notifications/{own_id}/read",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, response.text

    sync_db = db_manager.db.sync_db
    assert sync_db.notifications.find_one({"_id": own_id})["is_read"] is True
    assert sync_db.notifications.find_one({"_id": other_id})["is_read"] is False


def test_mark_all_read_is_scoped_to_current_user_and_tenant(client, student_token):
    own_id = _insert_notification("USR-TEST-STUDENT", "INST-DEFAULT")
    other_user_id = _insert_notification("USR-OTHER-STUDENT", "INST-DEFAULT")
    other_tenant_id = _insert_notification("USR-TEST-STUDENT", "INST-OTHER")

    response = client.put(
        "/api/notifications/mark-all-read",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200, response.text

    sync_db = db_manager.db.sync_db
    assert sync_db.notifications.find_one({"_id": own_id})["is_read"] is True
    assert sync_db.notifications.find_one({"_id": other_user_id})["is_read"] is False
    assert sync_db.notifications.find_one({"_id": other_tenant_id})["is_read"] is False
