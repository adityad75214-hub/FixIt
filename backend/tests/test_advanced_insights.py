from app.core.database import get_database


def test_ticket_classifier_returns_explainable_suggestions(client, student_token):
    response = client.post(
        "/api/advanced-insights/classify",
        json={"title": "Wi-Fi network not working", "description": "Internet connection drops in the computer lab."},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["method"] == "explainable_keyword_baseline"
    assert payload["is_trained_model"] is False
    if payload["suggestions"]:
        assert payload["suggestions"][0]["matched_terms"]


def test_staff_recommendations_only_include_qualified_tenant_staff(client, admin_token):
    response = client.post(
        "/api/advanced-insights/staff-recommendations",
        json={"category": "Network and Wi-Fi"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert all("Network and Wi-Fi" in item["specialization"] for item in payload["recommendations"])
    assert "USR-TEST-STAFF" in [item["staff_id"] for item in payload["recommendations"]]


def _observation_counts(observations):
    counts = {}
    for item in observations:
        if isinstance(item, dict):
            month, count = item["month"], item["tickets"]
        else:
            month, count = item
        counts[str(month)] = int(count)
    return counts


def test_forecast_requires_three_months_and_is_tenant_scoped(client, admin_token):
    import asyncio

    db = get_database()
    headers = {"Authorization": f"Bearer {admin_token}"}
    endpoint = "/api/advanced-insights/ticket-forecast"
    baseline_response = client.get(endpoint, headers=headers)
    assert baseline_response.status_code == 200
    baseline_counts = _observation_counts(baseline_response.json().get("observations", []))

    async def seed_forecast_tickets():
        await db.tickets.delete_many({"title": "forecast fixture"})
        for index, month in enumerate(("2026-08", "2026-09", "2026-10"), start=1):
            await db.tickets.insert_one({
                "_id": f"forecast-{month}",
                "ticket_id": f"TKT-FORECAST-FIXTURE-{index}",
                "institution_id": "INST-DEFAULT",
                "title": "forecast fixture",
                "created_at": f"{month}-15T12:00:00+00:00",
                "status": "open",
                "category": "Network and Wi-Fi",
            })
        await db.tickets.insert_one({
            "_id": "forecast-foreign",
            "ticket_id": "TKT-FORECAST-FIXTURE-FOREIGN",
            "institution_id": "INST-OTHER",
            "title": "forecast fixture",
            "created_at": "2026-11-15T12:00:00+00:00",
            "status": "open",
        })

    asyncio.run(seed_forecast_tickets())
    response = client.get(endpoint, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    observed_counts = _observation_counts(payload["observations"])
    for month in ("2026-08", "2026-09", "2026-10"):
        assert observed_counts[month] - baseline_counts.get(month, 0) == 1
    assert observed_counts.get("2026-11", 0) - baseline_counts.get("2026-11", 0) == 0


def test_advanced_insights_requires_authentication(client):
    response = client.get("/api/advanced-insights/ticket-forecast")
    assert response.status_code == 401
