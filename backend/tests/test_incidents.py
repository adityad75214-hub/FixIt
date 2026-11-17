def test_admin_can_create_and_update_master_incident(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/incidents",
        headers=headers,
        json={
            "title": "Campus Wi-Fi outage",
            "description": "Wireless connectivity is unavailable in the engineering block.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Block",
            "severity": "critical",
            "linked_ticket_ids": [],
        },
    )
    assert created.status_code == 201, created.text
    incident_id = created.json()["id"]
    assert created.json()["status"] == "investigating"

    updated = client.patch(
        f"/api/incidents/{incident_id}",
        headers=headers,
        json={"status": "identified"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "identified"

    listed = client.get("/api/incidents", headers=headers)
    assert listed.status_code == 200
    assert any(item["id"] == incident_id for item in listed.json())


def test_only_staff_and_admin_can_create_incidents(client, student_token):
    response = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Campus Wi-Fi outage",
            "description": "Wireless connectivity is unavailable in the engineering block.",
            "category": "Network and Wi-Fi",
        },
    )
    assert response.status_code == 403


def test_incident_links_ticket_and_prevents_linking_it_twice(client, student_token, admin_token):
    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    ticket_response = client.post(
        "/api/tickets?auto_assign=false",
        headers=student_headers,
        json={
            "title": "Wi-Fi unavailable in systems lab",
            "description": "The lab access point is not broadcasting the campus network.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Block",
            "floor": "Ground Floor",
            "room": "G01",
            "priority": "high",
        },
    )
    assert ticket_response.status_code == 201, ticket_response.text
    ticket = ticket_response.json()

    incident_response = client.post(
        "/api/incidents",
        headers=admin_headers,
        json={
            "title": "Engineering block wireless outage",
            "description": "Multiple reports indicate a common wireless outage in the engineering block.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Block",
            "severity": "high",
            "linked_ticket_ids": [ticket["ticket_id"]],
        },
    )
    assert incident_response.status_code == 201, incident_response.text
    assert incident_response.json()["linked_ticket_count"] == 1

    ticket_detail = client.get(f"/api/tickets/{ticket['id']}", headers=student_headers)
    assert ticket_detail.status_code == 200
    assert ticket_detail.json()["linked_incident_id"] == incident_response.json()["id"]

    duplicate_link = client.post(
        "/api/incidents",
        headers=admin_headers,
        json={
            "title": "Duplicate wireless incident",
            "description": "This should not claim a ticket already linked elsewhere.",
            "category": "Network and Wi-Fi",
            "linked_ticket_ids": [ticket["ticket_id"]],
        },
    )
    assert duplicate_link.status_code == 409


def test_incident_list_is_limited_to_staff_and_admin(client, staff_token, student_token):
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    staff_response = client.get("/api/incidents", headers=staff_headers)
    assert staff_response.status_code == 200

    student_response = client.get("/api/incidents", headers=student_headers)
    assert student_response.status_code == 403


def test_staff_can_create_master_incident(client, staff_token):
    response = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "title": "Staff-created campus network incident",
            "description": "Testing the documented staff incident creation permission.",
            "category": "Network and Wi-Fi",
            "severity": "medium",
            "linked_ticket_ids": [],
        },
    )
    assert response.status_code == 201, response.text
