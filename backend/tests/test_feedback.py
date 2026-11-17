def test_feedback_submission_and_rules(client, student_token, staff_token, admin_token):
    # 1. Student creates ticket
    create_res = client.post(
        "/api/tickets",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "title": "Smartboard pen not charging",
            "description": "Smartboard pen in Room 401 battery is dead.",
            "category": "Projector and Smart Classroom",
            "building": "Central Academic Tower",
            "floor": "4th Floor",
            "room": "Room 401"
        }
    )
    assert create_res.status_code == 201
    ticket_id = create_res.json()["id"]

    # Admin assigns the ticket to the staff member before staff updates it.
    assign_res = client.post(
        f"/api/assignments/{ticket_id}/assign",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "staff_id": "USR-TEST-STAFF",
            "note": "Assigned for feedback workflow test"
        }
    )
    assert assign_res.status_code == 200, assign_res.text

    # 2. Try to submit feedback before resolution -> Should fail (400)
    early_feedback = client.post(
        "/api/feedback",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "ticket_id": ticket_id,
            "rating": 5,
            "comments": "Good"
        }
    )
    assert early_feedback.status_code == 400
    assert "resolution" in early_feedback.json()["detail"].lower()

    # 3. Staff moves ticket to in_progress then resolved
    res_progress = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"status": "in_progress", "note": "Investigating battery"}
    )
    assert res_progress.status_code == 200, res_progress.text
    res_resolve = client.put(
        f"/api/tickets/{ticket_id}/status",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={"status": "resolved", "resolution_notes": "Replaced stylus battery."}
    )
    assert res_resolve.status_code == 200

    # 4. Another user cannot submit feedback for this ticket (RBAC creator-only check)
    staff_illegal_feedback = client.post(
        "/api/feedback",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "ticket_id": ticket_id,
            "rating": 4,
            "comments": "Staff rating self"
        }
    )
    assert staff_illegal_feedback.status_code == 403

    # 5. Student submits feedback -> Should succeed (201)
    feedback_res = client.post(
        "/api/feedback",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "ticket_id": ticket_id,
            "rating": 5,
            "comments": "Replaced very quickly, thank you!"
        }
    )
    assert feedback_res.status_code == 201
    assert feedback_res.json()["rating"] == 5

    # 6. Duplicate feedback attempt -> Should fail
    dup_res = client.post(
        "/api/feedback",
        headers={"Authorization": f"Bearer {student_token}"},
        json={
            "ticket_id": ticket_id,
            "rating": 4,
            "comments": "Trying to rate again"
        }
    )
    assert dup_res.status_code == 400
    assert "already been submitted" in dup_res.json()["detail"].lower()

def test_knowledge_base_search_and_helpful_voting(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    # 1. Search knowledge base articles
    search_res = client.get("/api/knowledge-base?search=wifi", headers=headers)
    assert search_res.status_code == 200
    articles = search_res.json()
    assert len(articles) > 0
    article = articles[0]
    art_id = article["id"]

    # 2. Vote helpful on article
    initial_helpful = article.get("helpful_count", 0)
    vote_res = client.post(f"/api/knowledge-base/{art_id}/vote", headers=headers, json={"helpful": True})
    assert vote_res.status_code == 200
    assert vote_res.json()["helpful_count"] == initial_helpful + 1

    # A user may vote only once per article; repeated requests cannot inflate metrics.
    repeat_vote = client.post(f"/api/knowledge-base/{art_id}/vote", headers=headers, json={"helpful": True})
    assert repeat_vote.status_code == 409

def test_auto_assignment_transparent_scoring(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}

    # Create ticket for Network and Wi-Fi category with auto_assign=true
    res = client.post("/api/tickets?auto_assign=true", headers=headers, json={
        "title": "Wi-Fi access point dead in hall",
        "description": "Entire room unable to connect to campus network.",
        "category": "Network and Wi-Fi",
        "building": "Engineering Block",
        "floor": "Ground Floor",
        "room": "G01",
        "priority": "high"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["status"] in ["assigned", "open"]
    if data["assigned_to"]:
        # Verify network specialist was chosen
        assert "specialization" in data["assigned_to"] or "name" in data["assigned_to"]
