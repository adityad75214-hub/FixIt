import pytest
from httpx import AsyncClient

def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "database" in data

def test_campus_hierarchy_retrieval(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    response = client.get("/api/campus/hierarchy", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "buildings" in data
    assert isinstance(data["buildings"], list)
    assert len(data["buildings"]) >= 4

    # Verify building floor counts vary (e.g. 2 floors, 4 floors, 5 floors)
    building_names = [b["name"] for b in data["buildings"]]
    assert "Administrative Building" in building_names
    assert "Engineering Block" in building_names
    assert "Science & Research Complex" in building_names

    adm_building = next(b for b in data["buildings"] if b["name"] == "Administrative Building")
    assert len(adm_building["floors"]) == 2

    sci_building = next(b for b in data["buildings"] if b["name"] == "Science & Research Complex")
    assert len(sci_building["floors"]) == 5

def test_admin_building_creation(client, admin_token, student_token):
    # Student cannot create buildings (RBAC check)
    student_headers = {"Authorization": f"Bearer {student_token}"}
    unauthorized_res = client.post("/api/campus/buildings", json={
        "campus_id": "CAMPUS-MAIN",
        "name": "Unauthorized Pavilion",
        "code": "UNAUTH",
        "total_floors": 1
    }, headers=student_headers)
    assert unauthorized_res.status_code == 403

    # Admin can create buildings
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    created_res = client.post("/api/campus/buildings", json={
        "campus_id": "CAMPUS-MAIN",
        "name": "Innovation Hub",
        "code": "IHUB",
        "total_floors": 3
    }, headers=admin_headers)
    assert created_res.status_code == 201
    created_data = created_res.json()
    assert created_data["name"] == "Innovation Hub"
    assert created_data["total_floors"] == 3


def test_campus_creation_is_admin_only(client, admin_token, student_token):
    import uuid

    campus_code = f"T{uuid.uuid4().hex[:8].upper()}"
    payload = {"name": "Test Campus", "code": campus_code, "is_active": True}

    denied = client.post(
        "/api/campus",
        json=payload,
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert denied.status_code == 403

    created = client.post(
        "/api/campus",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["code"] == campus_code


def test_campus_hierarchy_rejects_invalid_parent_relationships(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    invalid_building = client.post(
        "/api/campus/buildings",
        headers=headers,
        json={"campus_id": "CAMPUS-DOES-NOT-EXIST", "name": "Orphan Building", "code": "ORPH", "total_floors": 2},
    )
    assert invalid_building.status_code == 400

    invalid_floor = client.post(
        "/api/campus/floors",
        headers=headers,
        json={"building_id": "BLD-DOES-NOT-EXIST", "floor_number": 0, "floor_name": "Ground Floor"},
    )
    assert invalid_floor.status_code == 400

    invalid_room = client.post(
        "/api/campus/rooms",
        headers=headers,
        json={"building_id": "BLD-ADM", "floor_id": "FLR-ENG-0", "room_number": "X99", "room_name": "Wrong Building Room"},
    )
    assert invalid_room.status_code == 400


def test_admin_can_configure_blocks_and_block_specific_floors(client, admin_token):
    import uuid
    headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6].upper()
    campus = client.post("/api/campus", headers=headers, json={"name": f"Location Campus {suffix}", "code": f"LC{suffix}"})
    assert campus.status_code == 201, campus.text
    campus_id = campus.json()["id"]
    building = client.post("/api/campus/buildings", headers=headers, json={"campus_id": campus_id, "name": f"Academic Building {suffix}", "code": f"AB{suffix}", "total_floors": 3})
    assert building.status_code == 201, building.text
    building_id = building.json()["id"]
    block = client.post("/api/campus/blocks", headers=headers, json={"building_id": building_id, "name": "East Wing", "code": f"EW{suffix}"})
    assert block.status_code == 201, block.text
    floor = client.post("/api/campus/floors", headers=headers, json={"building_id": building_id, "block_id": block.json()["id"], "floor_number": 1, "floor_name": "First Floor"})
    assert floor.status_code == 201, floor.text
    hierarchy = client.get("/api/campus/hierarchy", headers=headers)
    building_node = next(item for item in hierarchy.json()["buildings"] if item["id"] == building_id)
    assert building_node["blocks"][0]["name"] == "East Wing"
    assert building_node["floors"][0]["block_id"] == block.json()["id"]


def test_admin_can_add_custom_locations_and_students_can_view_them(client, admin_token, student_token):
    import uuid
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    suffix = uuid.uuid4().hex[:6].upper()
    campus = client.post("/api/campus", headers=admin_headers, json={"name": f"Custom Location Campus {suffix}", "code": f"CL{suffix}"})
    campus_id = campus.json()["id"]
    building = client.post("/api/campus/buildings", headers=admin_headers, json={"campus_id": campus_id, "name": f"Hostel Building {suffix}", "code": f"HB{suffix}", "total_floors": 2})
    building_id = building.json()["id"]
    floor = client.post("/api/campus/floors", headers=admin_headers, json={"building_id": building_id, "floor_number": 1, "floor_name": "First Floor"})
    payload = {"campus_id": campus_id, "building_id": building_id, "floor_id": floor.json()["id"], "name": "Hostel Common Room", "code": f"HCR{suffix}", "category": "common_room", "description": "Student recreation area"}
    created = client.post("/api/campus/locations", headers=admin_headers, json=payload)
    assert created.status_code == 201, created.text
    student_headers = {"Authorization": f"Bearer {student_token}"}
    visible = client.get(f"/api/campus/locations?campus_id={campus_id}", headers=student_headers)
    assert visible.status_code == 200
    assert any(item["name"] == "Hostel Common Room" for item in visible.json())

    outdoor = client.post("/api/campus/locations", headers=admin_headers, json={
        "campus_id": campus_id, "name": "Main Gate", "code": f"MG{suffix}",
        "category": "gate", "description": "Main campus entrance"
    })
    assert outdoor.status_code == 201, outdoor.text
    ticket = client.post("/api/tickets?auto_assign=false", headers=student_headers, json={
        "title": "Main gate lighting is not working",
        "description": "The lights near the main gate are not working after sunset.",
        "problem_domain": "facilities",
        "category": "Campus Facilities and Maintenance",
        "campus_id": campus_id,
        "building": "Campus-wide / Outdoor",
        "floor": "Outdoor",
        "room": "Main Gate"
    })
    assert ticket.status_code == 201, ticket.text


def test_campus_and_ticket_data_are_isolated_between_institutions(client, admin_token):
    import uuid
    from app.core.database import get_database
    from app.core.security import create_access_token

    db = get_database()
    sync_db = db.sync_db
    institution_id = f"INST-TEST-{uuid.uuid4().hex[:8].upper()}"
    sync_db.institutions.insert_one({"_id": institution_id, "name": "Second College", "slug": f"second-{uuid.uuid4().hex[:6]}", "status": "active", "email_domains": []})
    second_admin_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    sync_db.users.insert_one({
        "_id": second_admin_id, "email": f"admin-{uuid.uuid4().hex[:6]}@second.edu",
        "name": "Second College Admin", "role": "admin", "institution_id": institution_id,
        "is_active": True, "token_version": 0, "created_at": "2026-01-01T00:00:00+00:00"
    })
    second_token = create_access_token({"sub": second_admin_id, "role": "admin", "ver": 0})
    second_headers = {"Authorization": f"Bearer {second_token}"}
    first_headers = {"Authorization": f"Bearer {admin_token}"}

    campus = client.post("/api/campus", headers=second_headers, json={"name": "Second Main Campus", "code": f"S{uuid.uuid4().hex[:6].upper()}"})
    assert campus.status_code == 201, campus.text
    second_campus_id = campus.json()["id"]

    first_campuses = client.get("/api/campus", headers=first_headers)
    assert first_campuses.status_code == 200
    assert all(item["id"] != second_campus_id for item in first_campuses.json())

    second_building = client.post("/api/campus/buildings", headers=second_headers, json={
        "campus_id": second_campus_id, "name": "Second College Hostel",
        "code": f"H{uuid.uuid4().hex[:5].upper()}", "total_floors": 1
    })
    assert second_building.status_code == 201, second_building.text
    second_block = client.post("/api/campus/blocks", headers=second_headers, json={
        "building_id": second_building.json()["id"], "name": "North Wing", "code": f"N{uuid.uuid4().hex[:5].upper()}"
    })
    assert second_block.status_code == 201, second_block.text
    second_floor = client.post("/api/campus/floors", headers=second_headers, json={
        "building_id": second_building.json()["id"], "block_id": second_block.json()["id"],
        "floor_number": 0, "floor_name": "Ground Floor"
    })
    assert second_floor.status_code == 201, second_floor.text
    second_room = client.post("/api/campus/rooms", headers=second_headers, json={
        "building_id": second_building.json()["id"], "floor_id": second_floor.json()["id"],
        "room_number": "G01", "room_name": "Private Room"
    })
    assert second_room.status_code == 201, second_room.text

    for endpoint in ("/api/campus/buildings", "/api/campus/blocks", "/api/campus/floors", "/api/campus/rooms"):
        visible = client.get(endpoint, headers=first_headers)
        assert visible.status_code == 200
        assert all(item["id"] not in {second_building.json()["id"], second_block.json()["id"], second_floor.json()["id"], second_room.json()["id"]} for item in visible.json())

    cross_building = client.post("/api/campus/buildings", headers=first_headers, json={
        "campus_id": second_campus_id, "name": "Unauthorized Building",
        "code": f"X{uuid.uuid4().hex[:5].upper()}", "total_floors": 1
    })
    assert cross_building.status_code == 400

    foreign_ticket_id = f"TCK-{uuid.uuid4().hex[:10].upper()}"
    sync_db.tickets.insert_one({
        "_id": foreign_ticket_id, "ticket_id": f"FOREIGN-{uuid.uuid4().hex[:6].upper()}",
        "institution_id": institution_id, "title": "Second college issue", "description": "Private issue",
        "category": "Facilities", "priority": "low", "status": "open", "building": "Hostel",
        "floor": "Ground", "room": "Common Room", "created_by": {"id": second_admin_id},
        "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00",
        "timeline": []
    })
    first_tickets = client.get("/api/tickets", headers=first_headers)
    assert first_tickets.status_code == 200
    assert all(item["id"] != foreign_ticket_id for item in first_tickets.json())
    hidden_ticket = client.get(f"/api/tickets/{foreign_ticket_id}", headers=first_headers)
    assert hidden_ticket.status_code == 404

    hidden_priority_update = client.put(f"/api/tickets/{foreign_ticket_id}/priority", headers=first_headers, json={"priority": "high", "reason": "tenant test"})
    assert hidden_priority_update.status_code == 404
    hidden_auto_assignment = client.post(f"/api/assignments/{foreign_ticket_id}/auto-assign", headers=first_headers)
    assert hidden_auto_assignment.status_code == 404

    foreign_article_id = f"KB-{uuid.uuid4().hex[:8].upper()}"
    sync_db.knowledge_base.insert_one({
        "_id": foreign_article_id, "institution_id": institution_id,
        "title": "Private college article", "category": "Facilities",
        "content": "This article belongs to another institution.",
        "is_published": True, "tags": [], "created_at": "2026-01-01T00:00:00+00:00"
    })
    hidden_article = client.get(f"/api/knowledge-base/{foreign_article_id}", headers=first_headers)
    assert hidden_article.status_code == 404

    first_users = client.get("/api/users", headers=first_headers)
    assert first_users.status_code == 200
    assert all(user["id"] != second_admin_id for user in first_users.json())

    foreign_notification_id = f"NOTIF-{uuid.uuid4().hex[:12].upper()}"
    sync_db.notifications.insert_one({
        "_id": foreign_notification_id, "user_id": "USR-TEST-ADMIN",
        "institution_id": institution_id, "title": "Foreign tenant notification",
        "message": "This should not be visible in the default workspace.",
        "is_read": False, "created_at": "2026-01-01T00:00:00+00:00"
    })
    notifications = client.get("/api/notifications", headers=first_headers)
    assert notifications.status_code == 200
    assert all(item["id"] != foreign_notification_id for item in notifications.json()["notifications"])


def test_platform_admin_can_onboard_college_and_provision_college_admin(client, monkeypatch):
    import re
    import uuid
    import app.services.notification_service as mailer
    from app.core.config import settings
    from app.core.database import get_database
    from app.core.security import create_access_token

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
    monkeypatch.setattr(settings, "SMTP_FROM_EMAIL", "noreply@fixit.example")
    monkeypatch.setattr(settings, "APP_BASE_URL", "https://fixit.example")
    sent = {}
    monkeypatch.setattr(mailer, "_send_email", lambda recipient, subject, body: sent.update(recipient=recipient, body=body))

    db = get_database()
    sync_db = db.sync_db
    platform_id = f"USR-PLATFORM-{uuid.uuid4().hex[:8].upper()}"
    sync_db.users.insert_one({
        "_id": platform_id, "email": f"platform-{uuid.uuid4().hex[:6]}@fixit.example",
        "name": "Platform Operator", "role": "platform_admin", "institution_id": "INST-PLATFORM",
        "is_active": True, "token_version": 0, "created_at": "2026-01-01T00:00:00+00:00"
    })
    platform_token = create_access_token({"sub": platform_id, "role": "platform_admin", "ver": 0})
    headers = {"Authorization": f"Bearer {platform_token}"}
    slug = f"college-{uuid.uuid4().hex[:7]}"
    created = client.post("/api/institutions", headers=headers, json={
        "name": "New College Workspace", "slug": slug, "email_domains": ["newcollege.edu"]
    })
    assert created.status_code == 201, created.text
    institution_id = created.json()["id"]

    duplicate_domain = client.post("/api/institutions", headers=headers, json={
        "name": "Duplicate Domain College", "slug": f"duplicate-{uuid.uuid4().hex[:6]}",
        "email_domains": ["newcollege.edu"]
    })
    assert duplicate_domain.status_code == 409

    admin = client.post(f"/api/institutions/{institution_id}/admins/invitations", headers=headers, json={
        "email": "admin@newcollege.edu", "name": "College Admin"
    })
    assert admin.status_code == 202, admin.text
    assert sent["recipient"] == "admin@newcollege.edu"
    raw_token = re.search(r"token=([^\s]+)", sent["body"]).group(1)
    accepted = client.post("/api/institutions/admin-invitations/accept", json={
        "token": raw_token, "password": "CollegeAdmin@123"
    })
    assert accepted.status_code == 201, accepted.text
    college_token = create_access_token({"sub": accepted.json()["user"]["id"], "role": "admin", "ver": 0})
    college_headers = {"Authorization": f"Bearer {college_token}"}

    campus = client.post("/api/campus", headers=college_headers, json={"name": "New College Campus", "code": "MAIN"})
    assert campus.status_code == 201, campus.text
    assert campus.json()["id"]
    categories = client.get("/api/categories", headers=college_headers)
    assert categories.status_code == 200
    assert categories.json(), "New college should receive its own default categories"

    managed = client.get("/api/institutions/manage", headers=headers)
    assert managed.status_code == 200
    assert any(item["id"] == institution_id for item in managed.json())
    suspended = client.put(f"/api/institutions/{institution_id}", headers=headers, json={"status": "suspended"})
    assert suspended.status_code == 200, suspended.text
    blocked = client.get("/api/campus", headers=college_headers)
    assert blocked.status_code == 403
    reactivated = client.put(f"/api/institutions/{institution_id}", headers=headers, json={"status": "active"})
    assert reactivated.status_code == 200, reactivated.text
    restored = client.get("/api/campus", headers=college_headers)
    assert restored.status_code == 200

    denied = client.post("/api/institutions", headers=college_headers, json={
        "name": "Unauthorized College", "slug": f"unauthorized-{uuid.uuid4().hex[:6]}", "email_domains": []
    })
    assert denied.status_code == 403



def test_suspended_institution_members_are_denied_api_access(client):
    import uuid
    from app.core.database import get_database
    from app.core.security import create_access_token

    db = get_database()
    sync_db = db.sync_db
    institution_id = f"INST-SUSP-{uuid.uuid4().hex[:8].upper()}"
    sync_db.institutions.insert_one({
        "_id": institution_id, "name": "Suspended College", "slug": f"suspended-{uuid.uuid4().hex[:6]}",
        "status": "suspended", "email_domains": []
    })
    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    sync_db.users.insert_one({
        "_id": user_id, "email": f"user-{uuid.uuid4().hex[:6]}@suspended.edu",
        "name": "Suspended User", "role": "student", "institution_id": institution_id,
        "is_active": True, "token_version": 0, "created_at": "2026-01-01T00:00:00+00:00"
    })
    token = create_access_token({"sub": user_id, "role": "student", "ver": 0})
    response = client.get("/api/campus", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403



def test_campus_structure_edit_is_safe_and_ticket_locations_cannot_be_deactivated(client, admin_token, student_token):
    import uuid

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}
    suffix = uuid.uuid4().hex[:7].upper()

    campus = client.post("/api/campus", headers=admin_headers, json={
        "name": f"Edit Campus {suffix}", "code": f"EC{suffix}"
    })
    assert campus.status_code == 201, campus.text
    campus_id = campus.json()["id"]

    building = client.post("/api/campus/buildings", headers=admin_headers, json={
        "campus_id": campus_id, "name": f"Edit Building {suffix}",
        "code": f"EB{suffix}", "total_floors": 1
    })
    assert building.status_code == 201, building.text
    building_id = building.json()["id"]

    floor = client.post("/api/campus/floors", headers=admin_headers, json={
        "building_id": building_id, "floor_number": 0, "floor_name": f"Ground {suffix}"
    })
    assert floor.status_code == 201, floor.text
    floor_id = floor.json()["id"]

    room = client.post("/api/campus/rooms", headers=admin_headers, json={
        "building_id": building_id, "floor_id": floor_id,
        "room_number": f"R{suffix}", "room_name": "Test Lab"
    })
    assert room.status_code == 201, room.text
    room_id = room.json()["id"]

    edited = client.put(f"/api/campus/rooms/{room_id}", headers=admin_headers, json={
        "room_number": f"R2{suffix}", "room_name": "Updated Test Lab"
    })
    assert edited.status_code == 200, edited.text
    assert edited.json()["room_number"] == f"R2{suffix}"

    # Parent references cannot be changed through the details editor.
    moved = client.put(f"/api/campus/rooms/{room_id}", headers=admin_headers, json={
        "building_id": "BLD-OTHER"
    })
    assert moved.status_code == 400, moved.text

    ticket = client.post("/api/tickets?auto_assign=false", headers=student_headers, json={
        "title": "Test lab projector has stopped working",
        "description": "The projector in this test lab no longer powers on.",
        "problem_domain": "facilities",
        "category": "Campus Facilities and Maintenance",
        "campus_id": campus_id,
        "building": f"Edit Building {suffix}",
        "floor": f"Ground {suffix}",
        "room": f"R2{suffix}"
    })
    assert ticket.status_code == 201, ticket.text

    blocked = client.delete(f"/api/campus/rooms/{room_id}", headers=admin_headers)
    assert blocked.status_code == 409, blocked.text
    assert "ticket" in blocked.json()["detail"].lower()

    # Tenant isolation and role authorization still apply to maintenance APIs.
    student_edit = client.put(f"/api/campus/rooms/{room_id}", headers=student_headers, json={
        "room_name": "Unauthorized"
    })
    assert student_edit.status_code == 403
