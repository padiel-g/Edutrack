import os

import pytest


os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-characters")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-that-is-at-least-32-characters")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


@pytest.fixture()
def app(monkeypatch):
    from app import create_app
    from app.config import Config

    class TestConfig(Config):
        TESTING = True
        CHECK_DATABASE_SCHEMA = False
        RATELIMIT_ENABLED = False

    application = create_app(TestConfig)
    with application.app_context():
        yield application


@pytest.fixture()
def client(app):
    return app.test_client()
