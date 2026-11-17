import pytest
from pydantic import ValidationError

from app.core.config import Settings


def valid_production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "s" * 64,
        "ALGORITHM": "HS256",
        "MONGODB_URI": "mongodb://fixit_app:this-is-a-strong-app-password-123456789@mongodb:27017/fixit_db?authSource=fixit_db",
        "DATABASE_NAME": "fixit_db",
        "FALLBACK_TO_MOCK_DB": False,
        "SEED_DEMO_DATA": False,
        "PUBLIC_REGISTRATION_ENABLED": False,
        "BACKEND_CORS_ORIGINS": ["https://fixit.example.com"],
        "ALLOWED_HOSTS": ["fixit.example.com"],
        "COOKIE_SECURE": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_valid_production_configuration_is_accepted():
    settings = valid_production_settings()
    assert settings.is_production is True
    assert settings.refresh_cookie_secure is True


@pytest.mark.parametrize(
    "override",
    [
        {"SECRET_KEY": ""},
        {"SECRET_KEY": "short"},
        {"FALLBACK_TO_MOCK_DB": True},
        {"SEED_DEMO_DATA": True},
        {"PUBLIC_REGISTRATION_ENABLED": True},
        {"BACKEND_CORS_ORIGINS": ["*"]},
        {"BACKEND_CORS_ORIGINS": ["http://fixit.example.com"]},
        {"ALLOWED_HOSTS": ["*"]},
        {"COOKIE_SECURE": False},
        {"MONGODB_URI": "mongodb://localhost:27017/fixit_db"},
    ],
)
def test_unsafe_production_configuration_is_rejected(override):
    with pytest.raises(ValidationError):
        valid_production_settings(**override)


@pytest.mark.parametrize(
    "override",
    [
        {"ALLOWED_HOSTS": ["fixit.example.com", "localhost"]},
        {"ALLOWED_HOSTS": ["https://fixit.example.com"]},
        {"BACKEND_CORS_ORIGINS": ["https://fixit.example.com/admin"]},
        {"APP_BASE_URL": "http://fixit.example.com"},
        {"SMTP_HOST": "smtp.example.com", "SMTP_FROM_EMAIL": "notifications@fixit.example.com"},
        {"SMTP_HOST": "smtp.example.com", "SMTP_FROM_EMAIL": "notifications@fixit.example.com", "APP_BASE_URL": "https://fixit.example.com", "SMTP_USERNAME": "mailer"},
    ],
)
def test_production_configuration_rejects_incomplete_or_unsafe_public_endpoints(override):
    with pytest.raises(ValidationError):
        valid_production_settings(**override)


def test_production_configuration_accepts_complete_smtp_settings():
    settings = valid_production_settings(
        APP_BASE_URL="https://fixit.example.com",
        SMTP_HOST="smtp.example.com",
        SMTP_PORT=587,
        SMTP_USERNAME="mailer",
        SMTP_PASSWORD="a-long-smtp-password",
        SMTP_FROM_EMAIL="notifications@fixit.example.com",
    )
    assert settings.APP_BASE_URL == "https://fixit.example.com"
