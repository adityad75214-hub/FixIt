def test_user_preferences_round_trip_for_all_supported_languages(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    supported_languages = ("en", "hi", "kn", "ta", "te", "ml", "mr", "bn")

    for language in supported_languages:
        payload = {
            "email_notifications": False,
            "in_app_notifications": True,
            "language": language,
        }
        updated = client.put("/api/auth/preferences", json=payload, headers=headers)
        assert updated.status_code == 200, updated.text
        assert updated.json() == payload

        fetched = client.get("/api/auth/preferences", headers=headers)
        assert fetched.status_code == 200, fetched.text
        assert fetched.json() == payload


def test_user_preferences_require_authentication(client):
    response = client.get("/api/auth/preferences")
    assert response.status_code == 401
