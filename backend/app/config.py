import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _resolve_database_url() -> str:
    """Resolve the PostgreSQL connection string.

    EduTrack supports PostgreSQL only. If ``DATABASE_URL`` is missing or points
    at a SQLite database, configuration loading fails fast with a clear error so
    operators cannot accidentally boot the app against the wrong engine.
    """

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is required. EduTrack supports PostgreSQL only."
        )

    normalised = url.strip()
    lowered = normalised.lower()

    if lowered.startswith("sqlite"):
        raise RuntimeError(
            "DATABASE_URL is required. EduTrack supports PostgreSQL only."
        )

    if not (lowered.startswith("postgresql://") or lowered.startswith("postgresql+")):
        raise RuntimeError(
            "DATABASE_URL must be a PostgreSQL connection string "
            "(postgresql://user:password@host:5432/database). "
            "EduTrack supports PostgreSQL only."
        )

    return normalised


def _required_secret(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required and must be provided through the environment.")
    if len(value) < 32:
        raise RuntimeError(f"{name} must contain at least 32 characters.")
    return value


class Config:
    ENV = os.getenv("FLASK_ENV", "production").lower()
    SECRET_KEY = _required_secret("SECRET_KEY")
    JWT_SECRET_KEY = _required_secret("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    SQLALCHEMY_DATABASE_URI = _resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "pool_pre_ping": True,
    }
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", os.getenv("FRONTEND_URL", "")).split(",")
        if origin.strip()
    ]
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "true" if ENV == "production" else "false").lower() == "true"
    TRUST_PROXY = os.getenv("TRUST_PROXY", "true" if ENV == "production" else "false").lower() == "true"
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    JWT_BLOCKLIST_STORAGE_URI = os.getenv("JWT_BLOCKLIST_STORAGE_URI", RATELIMIT_STORAGE_URI)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))
    MATERIAL_UPLOAD_PATH = os.path.abspath(os.getenv("MATERIAL_UPLOAD_PATH", "uploads/learning-materials"))
    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "5"))
    BACKUP_PATH = os.path.abspath(os.getenv("BACKUP_PATH", "backups"))
