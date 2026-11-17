
def test_users_can_submit_and_only_see_their_own_feature_requests(client, student_token, faculty_token, admin_token):
    student_headers = {"Authorization": f"Bearer {student_token}"}
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "title": "Add WhatsApp ticket updates",
        "description": "Send users ticket status updates through an opt-in WhatsApp integration.",
        "area": "Notifications",
    }

    created = client.post("/api/feature-requests", headers=student_headers, json=payload)
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]

    student_list = client.get("/api/feature-requests", headers=student_headers)
    assert student_list.status_code == 200
    assert [item["id"] for item in student_list.json()] == [request_id]

    faculty_list = client.get("/api/feature-requests", headers=faculty_headers)
    assert faculty_list.status_code == 200
    assert faculty_list.json() == []

    admin_list = client.get("/api/feature-requests", headers=admin_headers)
    assert admin_list.status_code == 200
    assert any(item["id"] == request_id for item in admin_list.json())


def test_only_admin_can_update_feature_request_status(client, student_token, admin_token):
    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/feature-requests",
        headers=student_headers,
        json={
            "title": "Add keyboard shortcuts",
            "description": "Provide keyboard shortcuts for common helpdesk actions and navigation.",
            "area": "Mobile Experience",
        },
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]

    denied = client.patch(
        f"/api/feature-requests/{request_id}",
        headers=student_headers,
        json={"status": "planned"},
    )
    assert denied.status_code == 403

    updated = client.patch(
        f"/api/feature-requests/{request_id}",
        headers=admin_headers,
        json={"status": "planned", "admin_note": "Review after the notification work."},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["status"] == "planned"

    # Administrator-only internal notes must not be returned to request owners.
    owner_view = client.get(f"/api/feature-requests", headers=student_headers)
    assert owner_view.status_code == 200
    assert "admin_note" not in owner_view.json()[0]
