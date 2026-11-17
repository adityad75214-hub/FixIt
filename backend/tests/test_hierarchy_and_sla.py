import pytest

def test_ticket_creation_with_valid_campus_hierarchy(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    res = client.post("/api/tickets", headers=headers, json={
        "title": "Projector HDMI cable detached from wall panel",
        "description": "HDMI port does not feed audio or video to ceiling projector.",
        "category": "Projector and Smart Classroom",
        "building": "Administrative Building",
        "floor": "Ground Floor",
        "room": "101",
        "priority": "critical"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["ticket_id"].startswith("FIXIT-")
    assert data["building"] == "Administrative Building"
    assert data["floor"] == "Ground Floor"
    assert data["room"] == "101"
    assert data["priority"] == "critical"
    assert data["sla_target_hours"] == 2  # Critical SLA from DB policy is 2 hours

def test_ticket_creation_rejects_invalid_campus_hierarchy(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    # Invalid floor: Administrative Building only has 2 floors (Ground Floor, 1st Floor). 5th Floor does not exist.
    invalid_floor_res = client.post("/api/tickets", headers=headers, json={
        "title": "Invalid Floor Request",
        "description": "Trying to create ticket on non-existent floor.",
        "category": "Network and Wi-Fi",
        "building": "Administrative Building",
        "floor": "5th Floor",
        "room": "101"
    })
    assert invalid_floor_res.status_code == 400
    assert "does not exist in building" in invalid_floor_res.json()["detail"]

    # Invalid room: Room 999 does not exist on Ground Floor of Administrative Building
    invalid_room_res = client.post("/api/tickets", headers=headers, json={
        "title": "Invalid Room Request",
        "description": "Trying to create ticket in non-existent room.",
        "category": "Network and Wi-Fi",
        "building": "Administrative Building",
        "floor": "Ground Floor",
        "room": "Room 999"
    })
    assert invalid_room_res.status_code == 400
    assert "not valid for floor" in invalid_room_res.json()["detail"]

def test_atomic_ticket_id_sequential_formatting(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    res1 = client.post("/api/tickets", headers=headers, json={
        "title": "First ticket sequential check",
        "description": "Verifying ticket ID sequential counter formatting.",
        "category": "Network and Wi-Fi",
        "building": "Engineering Block",
        "floor": "Ground Floor",
        "room": "G01",
        "priority": "medium"
    })
    assert res1.status_code == 201
    id1 = res1.json()["ticket_id"]

    res2 = client.post("/api/tickets", headers=headers, json={
        "title": "Second ticket sequential check",
        "description": "Verifying ticket ID sequential counter formatting next item.",
        "category": "Network and Wi-Fi",
        "building": "Engineering Block",
        "floor": "Ground Floor",
        "room": "G01",
        "priority": "medium"
    })
    assert res2.status_code == 201
    id2 = res2.json()["ticket_id"]

    # Ticket IDs should both have format FIXIT-YYYY-NNNN and be distinct
    assert id1 != id2
    prefix = id1.rsplit("-", 1)[0]
    num1 = int(id1.rsplit("-", 1)[1])
    num2 = int(id2.rsplit("-", 1)[1])
    assert num2 > num1


def test_ticket_location_must_belong_to_selected_campus(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    base_payload = {
        "title": "Campus scoped location validation",
        "description": "Confirm a building and room are resolved within the selected campus.",
        "category": "Network and Wi-Fi",
        "building": "Administrative Building",
        "floor": "Ground Floor",
        "room": "101",
    }

    valid = client.post("/api/tickets", headers=headers, json={**base_payload, "campus_id": "CAMPUS-MAIN"})
    assert valid.status_code == 201, valid.text
    assert valid.json()["campus_id"] == "CAMPUS-MAIN"

    invalid = client.post("/api/tickets", headers=headers, json={**base_payload, "campus_id": "CAMPUS-OTHER"})
    assert invalid.status_code == 400
