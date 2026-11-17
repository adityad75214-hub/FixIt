import pytest
from fastapi.testclient import TestClient

def test_full_ticket_end_to_end_lifecycle(client: TestClient, student_token: str, staff_token: str, admin_token: str):
    """
    Comprehensive End-to-End Test for FIXIT:
    1. Student submits a new ticket with valid campus hierarchy.
    2. Admin assigns ticket to staff member.
    3. Staff member accepts and transitions status: Assigned -> In Progress.
    4. Staff member posts an internal note (restricted to staff/admin).
    5. Student verifies internal note is NOT visible to student.
    6. Staff member posts a public update comment.
    7. Student verifies public update comment IS visible.
    8. Staff resolves ticket: In Progress -> Resolved.
    9. Student submits 1-5 star feedback with review.
    10. Verify second feedback attempt by student is rejected (one per ticket).
    11. Verify non-creator cannot submit feedback on this ticket.
    12. Admin closes ticket: Resolved -> Closed.
    13. Verify audit log captures entire lifecycle.
    """
    student_headers = {"Authorization": f"Bearer {student_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Student creates ticket
    ticket_payload = {
        "title": "Complete E2E Lifecycle Network Failure in Engineering Hall 101",
        "description": "Ethernet wall ports in Lab 101 have lost connectivity to the main switch.",
        "category": "Network & Wi-Fi",
        "subcategory": "Ethernet Port",
        "priority": "high",
        "building": "Engineering Hall",
        "floor": "1st Floor",
        "room": "Lab 101",
        "affected_users": 15
    }

    create_res = client.post("/api/tickets/", json=ticket_payload, headers=student_headers)
    assert create_res.status_code == 201, create_res.text
    ticket_data = create_res.json()
    ticket_id = ticket_data["id"]
    formatted_id = ticket_data["ticket_id"]
    assert formatted_id.startswith("FIXIT-")
    # Auto-assignment may assign immediately if an active specialized staff member exists, or leave open
    assert ticket_data["status"] in ["open", "assigned"]
    assert ticket_data["sla_target_hours"] == 8

    # Step 2: Ensure ticket is assigned to Staff (manual assignment / re-assignment)
    staff_profile = client.get("/api/auth/me", headers=staff_headers).json()
    staff_id = staff_profile["id"]

    assign_res = client.post(
        f"/api/assignments/{ticket_id}/assign",
        json={"staff_id": staff_id, "note": "Assigned to network engineer on duty"},
        headers=admin_headers
    )
    assert assign_res.status_code == 200, assign_res.text
    # Verify ticket status is now assigned
    ticket_after_assign = client.get(f"/api/tickets/{ticket_id}", headers=admin_headers).json()
    assert ticket_after_assign["status"] == "assigned"
    assigned_obj = ticket_after_assign["assigned_to"]
    if isinstance(assigned_obj, dict):
        assert assigned_obj["id"] == staff_id
    else:
        assert assigned_obj == staff_id

    # Step 3: Staff moves ticket to In Progress
    progress_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "in_progress", "note": "Started investigating switch rack port configuration"},
        headers=staff_headers
    )
    assert progress_res.status_code == 200, progress_res.text
    assert progress_res.json()["status"] == "in_progress"

    # Step 4: Staff adds an Internal Note
    internal_res = client.post(
        f"/api/comments/ticket/{ticket_id}",
        json={"content": "INTERNAL: Identified VLAN trunk mismatch on switch Cisco-3850.", "is_internal": True},
        headers=staff_headers
    )
    assert internal_res.status_code == 201, internal_res.text
    assert internal_res.json()["is_internal"] is True

    # Step 5: Student fetches comments - Internal Note MUST be hidden
    student_comments_res = client.get(f"/api/comments/ticket/{ticket_id}", headers=student_headers)
    assert student_comments_res.status_code == 200
    student_comments = student_comments_res.json()
    assert not any(c.get("is_internal") for c in student_comments)
    assert not any("VLAN trunk" in c.get("content", "") for c in student_comments)

    # Step 6: Staff adds a Public Comment
    public_res = client.post(
        f"/api/comments/ticket/{ticket_id}",
        json={"content": "We have identified the issue on the floor switch and are applying a configuration fix.", "is_internal": False},
        headers=staff_headers
    )
    assert public_res.status_code == 201, public_res.text
    assert public_res.json()["is_internal"] is False

    # Step 7: Student fetches comments - Public comment MUST be visible
    student_comments_res2 = client.get(f"/api/comments/ticket/{ticket_id}", headers=student_headers)
    assert student_comments_res2.status_code == 200
    student_comments2 = student_comments_res2.json()
    assert any("applying a configuration fix" in c.get("content", "") for c in student_comments2)

    # Step 8: Staff resolves the ticket
    resolve_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "resolved", "note": "Switch port re-tagged and connectivity restored. All 15 stations online."},
        headers=staff_headers
    )
    assert resolve_res.status_code == 200, resolve_res.text
    assert resolve_res.json()["status"] == "resolved"

    # Step 9: Student submits 5-star feedback
    feedback_payload = {
        "ticket_id": ticket_id,
        "rating": 5,
        "comments": "Excellent rapid resolution by network IT team!"
    }
    fb_res = client.post("/api/feedback/", json=feedback_payload, headers=student_headers)
    assert fb_res.status_code == 201, fb_res.text
    assert fb_res.json()["rating"] == 5

    # Step 10: Duplicate feedback attempt rejected
    dup_fb_res = client.post("/api/feedback/", json=feedback_payload, headers=student_headers)
    assert dup_fb_res.status_code == 400

    # Step 11: Non-creator cannot submit feedback
    staff_fb_res = client.post("/api/feedback/", json=feedback_payload, headers=staff_headers)
    assert staff_fb_res.status_code in [400, 403]

    # Step 12: Admin closes the ticket
    close_res = client.put(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "closed", "note": "Ticket lifecycle completed with confirmed student feedback."},
        headers=admin_headers
    )
    assert close_res.status_code == 200, close_res.text
    assert close_res.json()["status"] == "closed"

    # Step 13: Audit logs verification
    audit_res = client.get("/api/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert "logs" in audit_data or isinstance(audit_data, list)
    logs = audit_data["logs"] if "logs" in audit_data else audit_data
    assert len(logs) >= 3  # at least ticket created, assigned, and status updates
