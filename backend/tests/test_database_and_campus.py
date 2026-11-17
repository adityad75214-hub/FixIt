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
