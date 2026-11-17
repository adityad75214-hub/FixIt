def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_staff_can_create_and_manage_draft_articles(client, staff_token, student_token):
    created = client.post(
        "/api/knowledge-base",
        headers=_auth(staff_token),
        json={
            "title": "Campus Transport Support Guide",
            "category": "Administrative",
            "content": "Steps for requesting help with campus transport services.",
            "tags": ["transport", "campus"],
            "is_published": False,
        },
    )
    assert created.status_code == 201
    article_id = created.json()["id"]
    assert created.json()["is_published"] is False

    staff_list = client.get("/api/knowledge-base", headers=_auth(staff_token))
    assert any(item["id"] == article_id for item in staff_list.json())

    student_list = client.get("/api/knowledge-base", headers=_auth(student_token))
    assert all(item["id"] != article_id for item in student_list.json())

    published = client.put(
        f"/api/knowledge-base/{article_id}",
        headers=_auth(staff_token),
        json={"is_published": True, "title": "Campus Transport Support Guide Updated"},
    )
    assert published.status_code == 200
    assert published.json()["is_published"] is True
    assert published.json()["title"].endswith("Updated")


def test_only_admin_can_delete_knowledge_base_articles(client, admin_token, staff_token):
    created = client.post(
        "/api/knowledge-base",
        headers=_auth(staff_token),
        json={
            "title": "Student Services Contact Guide",
            "category": "Student Support",
            "content": "Contact the relevant student services team for assistance.",
            "tags": ["student-services"],
        },
    )
    assert created.status_code == 201
    article_id = created.json()["id"]

    forbidden = client.delete(f"/api/knowledge-base/{article_id}", headers=_auth(staff_token))
    assert forbidden.status_code == 403

    deleted = client.delete(f"/api/knowledge-base/{article_id}", headers=_auth(admin_token))
    assert deleted.status_code == 200

    missing = client.delete(f"/api/knowledge-base/{article_id}", headers=_auth(admin_token))
    assert missing.status_code == 404
