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


@__import__('pytest').mark.asyncio
async def test_forecast_requires_three_months_and_is_tenant_scoped(client, admin_token):
    db = get_database()
    await db.tickets.delete_many({"institution_id": "INST-DEFAULT", "title": "forecast fixture"})
    for month in ("2026-08", "2026-09", "2026-10"):
        await db.tickets.insert_one({
            "_id": f"forecast-{month}", "institution_id": "INST-DEFAULT",
            "title": "forecast fixture", "created_at": f"{month}-15T12:00:00+00:00",
            "status": "open", "category": "Network and Wi-Fi",
        })
    # A foreign-tenant ticket must not affect the local forecast.
    await db.tickets.insert_one({
        "_id": "forecast-foreign", "institution_id": "INST-OTHER",
        "title": "forecast fixture", "created_at": "2026-11-15T12:00:00+00:00",
        "status": "open",
    })
    response = client.get(
        "/api/advanced-insights/ticket-forecast",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    observed_months = {item["month"] for item in payload["observations"]}
    assert {"2026-08", "2026-09", "2026-10"}.issubset(observed_months)
    assert sum(item["tickets"] for item in payload["observations"]) >= 3


def test_advanced_insights_requires_authentication(client):
    response = client.get("/api/advanced-insights/ticket-forecast")
    assert response.status_code == 401
