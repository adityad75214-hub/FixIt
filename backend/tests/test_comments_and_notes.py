def test_public_and_internal_notes_visibility(client, student_token, staff_token, admin_token):
    # Student creates ticket
    create_res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Software installation issue in Lab B",
            "description": "Visual Studio Code fails to install Python extension.",
            "category": "Software and Applications",
            "building": "Science & Tech Block",
            "floor": "1st Floor",
            "room": "Room 301"
        }
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Staff may comment only after the administrator assigns the ticket.
    assignment_res = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"staff_id": "USR-TEST-STAFF", "note": "Assign for comments visibility test"}
    )
    assert assignment_res.status_code == 200, assignment_res.text

    # Staff adds a public comment
    pub_res = client.post(
        f"/api/comments/ticket/{ticket_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "content": "Please check if your machine has proxy settings configured.",
            "is_internal": False
        }
    )
    assert pub_res.status_code == 201

    # Staff adds an INTERNAL note
    priv_res = client.post(
        f"/api/comments/ticket/{ticket_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "content": "CONFIDENTIAL: Lab B network switch firmware needs an update this weekend.",
            "is_internal": True
        }
    )
    assert priv_res.status_code == 201

    # Student cannot add internal note (RBAC check)
    student_illegal_note = client.post(
        f"/api/comments/ticket/{ticket_id}",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "content": "Trying to write internal note as student",
            "is_internal": True
        }
    )
    assert student_illegal_note.status_code == 403

    # Student requests comments: MUST ONLY see the public comment, NEVER the internal note!
    student_view = client.get(
        f"/api/comments/ticket/{ticket_id}",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert student_view.status_code == 200
    student_comments = student_view.json()
    assert len(student_comments) == 1
    assert student_comments[0]["is_internal"] is False
    assert "CONFIDENTIAL" not in student_comments[0]["content"]

    # Staff requests comments: CAN see both comments!
    staff_view = client.get(
        f"/api/comments/ticket/{ticket_id}",
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert staff_view.status_code == 200
    staff_comments = staff_view.json()
    assert len(staff_comments) == 2

def test_manual_ticket_assignment_and_notification(client, admin_token, staff_token, student_token):
    # Student creates ticket
    create_res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Ethernet drop defective in Dean office",
            "description": "Port does not provide link light when plugged in.",
            "category": "Network and Wi-Fi",
            "building": "Administrative Building",
            "floor": "Ground Floor",
            "room": "101"
        }
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Admin manually assigns ticket to staff
    assign_res = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "staff_id": "USR-TEST-STAFF",
            "note": "Assigned to network engineer for immediate dispatch"
        }
    )
    assert assign_res.status_code == 200

    # Staff checks notifications
    notif_res = client.get("/api/notifications", headers={"Authorization": f"Bearer {staff_token}"})
    assert notif_res.status_code == 200
    notifs = notif_res.json()["notifications"]
    assert any("Ticket Assigned" in n["title"] for n in notifs)

    # Staff updates ticket status to IN_PROGRESS
    status_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "status": "in_progress",
            "note": "On site replacing keystone jack"
        }
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "in_progress"


def test_student_cannot_read_or_comment_on_another_users_ticket(client, student_token, faculty_token):
    created = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Private ticket access control test",
            "description": "This ticket belongs to another account.",
            "category": "Software and Applications",
            "building": "Science & Tech Block",
            "floor": "1st Floor",
            "room": "Room 301"
        }
    )
    assert created.status_code == 201, created.text
    ticket_id = created.json()["id"]
    other_user_headers = {"Authorization": f"Bearer {faculty_token}"}

    read_result = client.get(f"/api/comments/ticket/{ticket_id}", headers=other_user_headers)
    assert read_result.status_code == 403

    write_result = client.post(
        f"/api/comments/ticket/{ticket_id}",
        headers=other_user_headers,
        json={"content": "Unauthorized comment attempt", "is_internal": False}
    )
    assert write_result.status_code == 403
