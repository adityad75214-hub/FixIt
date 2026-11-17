def test_ticket_creation_and_unique_id(client, student_token):
    res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Computer won't turn on in lab",
            "description": "The power button on workstation 5 does not respond at all.",
            "category": "Computer and Hardware",
            "priority": "medium",
            "building": "Engineering Hall",
            "floor": "1st Floor",
            "room": "Lab 102",
            "affected_users": 1
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert "ticket_id" in data
    assert data["ticket_id"].startswith("FIXIT-")
    assert data["status"] in ["open", "assigned"]
    assert data["created_by"]["email"] == "test.student@college.edu"
    assert len(data["timeline"]) >= 1

def test_duplicate_complaint_detection(client, student_token):
    # Test checking for duplicates
    res = client.post(
        "/api/tickets/check-duplicates",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Computer won't turn on in lab",
            "category": "Computer and Hardware",
            "building": "Engineering Hall",
            "room": "Lab 102"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "potential_duplicates" in data
    assert isinstance(data["potential_duplicates"], list)

def test_student_cannot_view_another_students_ticket(client, student_token, faculty_token):
    # Faculty creates a ticket
    create_res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {faculty_token}"},
        json={
            "title": "Faculty Department Projector Defective",
            "description": "Flickering HDMI connection in meeting room 301.",
            "category": "Projector and Smart Classroom",
            "priority": "high",
            "building": "Science & Tech Block",
            "room": "Room 301",
            "affected_users": 15
        }
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Student attempts to access faculty's ticket directly
    access_res = client.get(
        f"/api/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert access_res.status_code == 403
    assert "Access denied" in access_res.json()["detail"]

def test_ticket_status_transitions(client, staff_token, student_token, admin_token):
    # Student creates ticket
    create_res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Ethernet port damaged on desk 4",
            "description": "Physical RJ45 clip is broken on desk 4.",
            "category": "Network and Wi-Fi",
            "priority": "low",
            "building": "Engineering Hall",
            "room": "Lab 101"
        }
    )
    ticket_id = create_res.json()["id"]

    # Admin assigns the ticket to the staff member before staff updates it.
    assign_res = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "staff_id": "USR-TEST-STAFF",
            "note": "Assigned for status workflow test"
        }
    )
    assert assign_res.status_code == 200, assign_res.text

    # Staff updates status to in_progress
    status_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "status": "in_progress",
            "note": "Replaced the faceplate and testing with fluke meter."
        }
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "in_progress"

    # Staff updates status to resolved
    resolve_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "status": "resolved",
            "resolution_notes": "Port re-terminated and patch cable replaced."
        }
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

    # Student confirms resolution and closes ticket
    close_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "status": "closed",
            "note": "Verified, internet working great."
        }
    )
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "closed"


def test_duplicate_detection_does_not_leak_other_users_ticket_details(client, student_token, faculty_token):
    title = "Network outage in Engineering Lab 101"
    created = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": title,
            "description": "The lab network is unavailable.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Block",
            "floor": "1st Floor",
            "room": "101"
        }
    )
    assert created.status_code == 201, created.text

    check = client.post(
        "/api/tickets/check-duplicates",
        headers={"Authorization": f"Bearer {faculty_token}"},
        json={
            "title": title,
            "category": "Network and Wi-Fi",
            "building": "Engineering Block",
            "room": "101"
        }
    )
    assert check.status_code == 200
    data = check.json()
    assert data["potential_duplicates"] == []
    assert data["has_restricted_matches"] is True
    assert title not in check.text
    assert created.json()["id"] not in check.text
