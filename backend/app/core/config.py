from pathlib import Path
import secrets
from typing import List, Optional, Literal
from urllib.parse import urlsplit, unquote

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FixIt - Campus Support Platform"
    API_V1_STR: str = "/api"
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "fixit_db"
    FALLBACK_TO_MOCK_DB: bool = True

    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    COOKIE_SECURE: Optional[bool] = None
    COOKIE_SAMESITE: str = "lax"
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SEED_DEMO_DATA: bool = True
    PUBLIC_REGISTRATION_ENABLED: bool = True
    DOCS_ENABLED: bool = True

    APP_BASE_URL: Optional[str] = None

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_STARTTLS: bool = True

    SLA_CRITICAL_HOURS: int = 2
    SLA_HIGH_HOURS: int = 8
    SLA_MEDIUM_HOURS: int = 24
    SLA_LOW_HOURS: int = 72
    
    
    model_config = SettingsConfigDict(
    env_file=Path(__file__).resolve().parents[2] / ".env",
    env_file_encoding="utf-8",
    case_sensitive=True,
    extra="ignore",
)

    @model_validator(mode="after")
    def validate_security_configuration(self):
        production = self.ENVIRONMENT.lower() == "production"
        if not self.SECRET_KEY:
            if production:
                raise ValueError("SECRET_KEY must be set in production")
            self.SECRET_KEY = secrets.token_urlsafe(48)
        if production:
            if len(self.SECRET_KEY) < 64 or self.SECRET_KEY.lower().startswith(("replace_with", "generate-a-random", "changeme", "your-secret")):
                raise ValueError("Production SECRET_KEY must be a unique random value of at least 64 characters; example placeholders are not accepted")
            if self.ALGORITHM != "HS256":
                raise ValueError("Production ALGORITHM must be HS256")
            mongo_uri = urlsplit(self.MONGODB_URI)
            if mongo_uri.scheme not in {"mongodb", "mongodb+srv"} or not mongo_uri.hostname or not mongo_uri.username or not mongo_uri.password:
                raise ValueError("Production MONGODB_URI must include a remote host and database credentials")
            if mongo_uri.hostname.lower() in {"localhost", "127.0.0.1"}:
                raise ValueError("Production MONGODB_URI cannot point to localhost")
            mongo_password = unquote(mongo_uri.password or "")
            if len(mongo_password) < 24 or "replace_with" in mongo_password.lower():
                raise ValueError("Production MongoDB application password must be unique, random, and at least 24 characters")
            if not self.ALLOWED_HOSTS or "*" in self.ALLOWED_HOSTS:
                raise ValueError("Production ALLOWED_HOSTS must explicitly list trusted hostnames")
            if self.FALLBACK_TO_MOCK_DB:
                raise ValueError("FALLBACK_TO_MOCK_DB must be false in production")
            if self.SEED_DEMO_DATA:
                raise ValueError("SEED_DEMO_DATA must be false in production")
            if self.PUBLIC_REGISTRATION_ENABLED:
                if not self.SMTP_HOST or not (self.SMTP_FROM_EMAIL or self.SMTP_USERNAME) or not self.APP_BASE_URL:
                    raise ValueError("Public registration requires SMTP_HOST, a sender email, and APP_BASE_URL so institutional email verification can be delivered")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Wildcard CORS origins are not allowed in production")
            for origin in self.BACKEND_CORS_ORIGINS:
                parsed_origin = urlsplit(origin)
                if parsed_origin.scheme != "https" or not parsed_origin.hostname or parsed_origin.path not in ("", "/") or parsed_origin.query or parsed_origin.fragment:
                    raise ValueError("Production CORS origins must be HTTPS origins without paths or query strings")
            loopback_hosts = {"localhost", "127.0.0.1", "::1"}
            if any("://" in host or "/" in host for host in self.ALLOWED_HOSTS):
                raise ValueError("Production ALLOWED_HOSTS must contain hostnames, not URLs")
            if not any(host.strip().lower() not in loopback_hosts for host in self.ALLOWED_HOSTS):
                raise ValueError("Production ALLOWED_HOSTS must include at least one public hostname")
            if self.APP_BASE_URL:
                app_url = urlsplit(self.APP_BASE_URL)
                if app_url.scheme != "https" or not app_url.hostname or app_url.username or app_url.password:
                    raise ValueError("Production APP_BASE_URL must be a valid HTTPS URL")
            if self.SMTP_HOST:
                if not 1 <= self.SMTP_PORT <= 65535:
                    raise ValueError("SMTP_PORT must be between 1 and 65535")
                if not (self.SMTP_FROM_EMAIL or self.SMTP_USERNAME):
                    raise ValueError("SMTP requires SMTP_FROM_EMAIL or SMTP_USERNAME as the sender")
                if bool(self.SMTP_USERNAME) != bool(self.SMTP_PASSWORD):
                    raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")
                if not self.APP_BASE_URL:
                    raise ValueError("APP_BASE_URL is required when production email notifications are enabled")
            if self.COOKIE_SECURE is False:
                raise ValueError("COOKIE_SECURE cannot be false in production")
            if self.COOKIE_SAMESITE.lower() not in {"lax", "strict", "none"}:
                raise ValueError("COOKIE_SAMESITE must be lax, strict, or none")
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def refresh_cookie_secure(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.is_production


settings = Settings()
