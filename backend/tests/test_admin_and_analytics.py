import uuid
from datetime import datetime, timezone
from app.core.database import db_manager

def test_admin_audit_logs_access_and_rbac(client, admin_token, student_token):
    # Student cannot view audit logs (RBAC check)
    student_res = client.get("/api/audit-logs", headers={"Authorization": f"Bearer {student_token}"})
    assert student_res.status_code == 403

    # Admin can view audit logs
    admin_res = client.get("/api/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)

def test_analytics_dashboard_metrics(client, admin_token, student_token):
    # Student cannot access analytics dashboard
    student_res = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {student_token}"})
    assert student_res.status_code == 403

    # Admin can access analytics dashboard
    admin_res = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert "kpis" in data
    assert "charts" in data
    assert "monthly_trends" in data["charts"]
    assert "category_distribution" in data["charts"]
    assert "building_distribution" in data["charts"]

def test_csv_export_respects_filters(client, admin_token, student_token):
    # Student cannot export reports
    student_res = client.get("/api/reports/export/csv", headers={"Authorization": f"Bearer {student_token}"})
    assert student_res.status_code == 403

    # Admin can export CSV with active status/priority filters
    admin_res = client.get("/api/reports/export/csv?priority=critical", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert "text/csv" in admin_res.headers.get("content-type", "")
    assert "attachment" in admin_res.headers.get("content-disposition", "")
    content = admin_res.text
    # Verify CSV headers are present
    assert "Ticket ID,Title,Category,Priority,Status,Building,Room" in content


def test_staff_cannot_read_or_reassign_ticket_owned_by_another_technician(client, admin_token, staff_token, student_token):
    # Seed a second technician directly as test data. Production staff creation
    # is invitation-only, so this test must not bypass that API policy.
    second_staff_id = f"USR-SECOND-TECH-{uuid.uuid4().hex[:8].upper()}"
    db_manager.db.sync_db.users.insert_one({
        "_id": second_staff_id,
        "email": f"second.technician.{uuid.uuid4().hex[:8]}@college.edu",
        "name": "Second Technician",
        "role": "staff",
        "department": "IT Support",
        "specialization": ["Network and Wi-Fi"],
        "institution_id": "INST-DEFAULT",
        "is_active": True,
        "token_version": 0,
    })

    created_ticket = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Technician assignment isolation test",
            "description": "Verify a technician cannot access another technician's assigned ticket.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Hall",
            "floor": "1st Floor",
            "room": "Lab 101"
        }
    )
    assert created_ticket.status_code == 201, created_ticket.text
    ticket_id = created_ticket.json()["id"]

    assigned = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"staff_id": second_staff_id, "note": "Assign to second technician"}
    )
    assert assigned.status_code == 200, assigned.text

    other_staff_headers = {"Authorization": f"Bearer {staff_token}"}
    detail = client.get(f"/api/tickets/{ticket_id}", headers=other_staff_headers)
    assert detail.status_code == 403

    reassign = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers=other_staff_headers,
        json={"staff_id": "USR-TEST-STAFF", "note": "Unauthorized reassignment"}
    )
    assert reassign.status_code == 403


def test_admin_cannot_assign_ticket_to_deactivated_staff(client, admin_token, student_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    created_ticket = client.post(
        "/api/tickets",
        headers=student_headers,
        json={
            "title": "Deactivated technician assignment guard",
            "description": "Confirm that inactive technicians cannot receive new assignments.",
            "category": "Network and Wi-Fi",
            "building": "Engineering Hall",
            "floor": "Ground",
            "room": "Lab 101",
        },
    )
    assert created_ticket.status_code == 201, created_ticket.text

    deactivated = client.put(
        "/api/users/USR-TEST-STAFF",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert deactivated.status_code == 200, deactivated.text

    assignment = client.post(
        f"/api/assignments/{created_ticket.json()['id']}/assign",
        headers=admin_headers,
        json={"staff_id": "USR-TEST-STAFF", "note": "This should be rejected"},
    )
    assert assignment.status_code == 404


def test_admin_cannot_deactivate_own_admin_account(client, admin_token):
    response = client.put(
        "/api/users/USR-TEST-ADMIN",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert response.status_code == 400
    assert "own administrator account" in response.json()["detail"]


def test_analytics_counts_tickets_beyond_previous_2000_record_cap(client, admin_token):
    sync_db = db_manager.db.sync_db
    baseline = sync_db.tickets.count_documents({"institution_id": "INST-DEFAULT"})
    run_id = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "_id": f"ANALYTICS-LIMIT-{run_id}-{index}",
            "institution_id": "INST-DEFAULT",
            "ticket_id": f"FIXIT-ANALYTICS-LIMIT-{run_id}-{index}",
            "title": "Analytics scale verification",
            "description": "Synthetic record used to verify complete aggregation.",
            "category": "General IT Services",
            "priority": "low",
            "status": "open",
            "building": "Test Building",
            "room": "Test Room",
            "created_by": {"id": "USR-TEST-STUDENT", "name": "Test Student", "role": "student"},
            "created_at": now,
            "updated_at": now,
            "sla_deadline": now,
        }
        for index in range(2005)
    ]
    sync_db.tickets.insert_many(docs)

    response = client.get("/api/analytics/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, response.text
    assert response.json()["kpis"]["total_tickets"] == baseline + len(docs)


def test_feedback_metrics_include_reviews_beyond_previous_1000_record_cap(client, admin_token):
    sync_db = db_manager.db.sync_db
    baseline = sync_db.feedback.count_documents({"institution_id": "INST-DEFAULT"})
    baseline_fives = sync_db.feedback.count_documents({"institution_id": "INST-DEFAULT", "rating": 5})
    run_id = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "_id": f"METRICS-LIMIT-{run_id}-{index}",
            "institution_id": "INST-DEFAULT",
            "ticket_id": f"FIXIT-METRICS-LIMIT-{run_id}-{index}",
            "rating": 5,
            "comments": None,
            "created_by": {"id": "USR-TEST-STUDENT", "name": "Test Student"},
            "created_at": now,
        }
        for index in range(1005)
    ]
    sync_db.feedback.insert_many(docs)

    response = client.get("/api/feedback/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_reviews"] == baseline + len(docs)
    assert data["distribution"]["5"] == baseline_fives + len(docs)
    assert len(data["recent_reviews"]) <= 10


def test_csv_export_streams_all_tickets_beyond_previous_1000_record_cap(client, admin_token):
    sync_db = db_manager.db.sync_db
    run_id = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()
    docs = [
        {
            "_id": f"CSV-LIMIT-{run_id}-{index}",
            "institution_id": "INST-DEFAULT",
            "ticket_id": f"FIXIT-CSV-LIMIT-{run_id}-{index}",
            "title": "CSV scale verification",
            "category": "General IT Services",
            "priority": "low",
            "status": "open",
            "building": "Test Building",
            "room": "Test Room",
            "created_by": {"id": "USR-TEST-STUDENT", "name": "Test Student", "role": "student"},
            "created_at": now,
            "sla_deadline": now,
        }
        for index in range(1005)
    ]
    sync_db.tickets.insert_many(docs)

    response = client.get("/api/reports/export/csv", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200, response.text
    rows = response.text.splitlines()
    assert len(rows) >= len(docs) + 1
    assert sum(1 for row in rows if "CSV scale verification" in row) == len(docs)
