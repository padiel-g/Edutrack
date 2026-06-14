from types import SimpleNamespace
from unittest.mock import patch

import pytest
from flask_jwt_extended import create_access_token

from app.routes.crud import READ_ROLES, can_read_resource, validate_write_payload
from app.utils.credentials import generate_temporary_password, is_strong_password


ALL_ROLES = ["Super Admin", "Admin", "Accounts Officer", "Teacher", "Parent", "Student"]


@pytest.mark.parametrize("resource,allowed_roles", sorted(READ_ROLES.items()))
@pytest.mark.parametrize("role", ALL_ROLES)
def test_authorization_matrix_is_default_deny(resource, allowed_roles, role):
    assert can_read_resource(resource, role) is (role in allowed_roles)
    assert can_read_resource(resource, "Unknown Role") is False


@pytest.mark.parametrize(
    "field",
    [
        "id", "password_hash", "parent_password_hash", "created_at", "updated_at",
        "created_by_id", "updated_by_id", "role_id", "passwordHash", "roleId",
    ],
)
def test_generic_writes_reject_protected_fields(field):
    payload, error = validate_write_payload("users", {field: "attacker-value"})
    assert payload is None
    assert "Protected fields" in error


def test_generic_writes_reject_unknown_fields():
    payload, error = validate_write_payload("students", {"totally_unexpected": "value"})
    assert payload is None
    assert "Unsupported fields" in error


def test_temporary_passwords_are_unique_and_strong():
    values = {generate_temporary_password() for _ in range(25)}
    assert len(values) == 25
    assert "Edutrack" not in values
    assert all(is_strong_password(value) for value in values)


def test_unknown_role_cannot_list_resources(client, app):
    with app.app_context():
        token = create_access_token(
            identity="999",
            additional_claims={"role": "Unknown Role", "permissions": [], "mustChangePassword": False},
        )
    with patch("app.db.session.get", return_value=SimpleNamespace(token_version=0)):
        response = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_accounts_cannot_read_academic_results(client, app):
    with app.app_context():
        token = create_access_token(
            identity="11",
            additional_claims={"role": "Accounts Officer", "permissions": [], "mustChangePassword": False},
        )
    response = client.get("/api/exam-results", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_logout_revokes_token(client, app):
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "Admin", "permissions": [], "mustChangePassword": False},
        )
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.routes.auth.write_audit"), patch("app.routes.auth.db.session.commit"):
        response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    revoked = client.get("/api/auth/me", headers=headers)
    assert revoked.status_code == 401
    assert revoked.get_json()["error"] == "Token revoked"


def test_token_version_revokes_all_older_account_tokens(client, app):
    with app.app_context():
        token = create_access_token(
            identity="21",
            additional_claims={
                "role": "Teacher",
                "permissions": [],
                "mustChangePassword": False,
                "tokenVersion": 2,
            },
        )
    with patch("app.db.session.get", return_value=SimpleNamespace(token_version=3)):
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.get_json()["error"] == "Token revoked"


def test_must_change_password_claim_blocks_other_api_routes(client, app):
    with app.app_context():
        token = create_access_token(
            identity="12",
            additional_claims={"role": "Accounts Officer", "permissions": [], "mustChangePassword": True},
        )
    with patch("app.db.session.get", return_value=SimpleNamespace(token_version=0)):
        response = client.get("/api/students", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.get_json()["error"] == "Password change required"


def test_list_serializers_do_not_issue_per_row_queries(app):
    from app.models import SchoolClass, Teacher

    classes = [
        SchoolClass(id=index, name=f"Form {index}", grade_level=index, capacity=35)
        for index in range(1, 101)
    ]
    teachers = [
        Teacher(
            id=index,
            employee_number=f"T-{index:03d}",
            first_name="Test",
            last_name=f"Teacher {index}",
            email=f"teacher{index}@example.com",
        )
        for index in range(1, 101)
    ]
    with app.app_context(), patch("app.models.core.db.session.execute") as execute:
        for item in classes:
            item.subjects = []
            item.assigned_teachers = []
            item.to_dict()
        for item in teachers:
            item.subjects = []
            item.assigned_classes = []
            item.class_teacher_classes = []
            item.to_dict()
    execute.assert_not_called()


def test_readiness_checks_postgresql(client):
    response = client.get("/api/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_prometheus_metrics_are_exposed(client):
    client.get("/api/health")
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert b"edutrack_http_requests_total" in response.data


def test_production_rejects_memory_rate_limit_storage():
    from flask import Flask

    from app import validate_production_config

    app = Flask(__name__)
    app.config.update(TESTING=False, ENV="production", RATELIMIT_STORAGE_URI="memory://")
    with pytest.raises(RuntimeError, match="shared storage"):
        validate_production_config(app)


def test_production_rejects_memory_jwt_blocklist(monkeypatch):
    from flask import Flask

    from app import validate_production_config

    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "redis://redis:6379/0")
    app = Flask(__name__)
    app.config.update(
        TESTING=False,
        ENV="production",
        RATELIMIT_STORAGE_URI="redis://redis:6379/0",
        JWT_BLOCKLIST_STORAGE_URI="memory://",
    )
    with pytest.raises(RuntimeError, match="JWT_BLOCKLIST_STORAGE_URI"):
        validate_production_config(app)


def test_account_lockout_after_repeated_failures():
    from app.routes.auth import register_failed_login

    account = SimpleNamespace(failed_login_attempts=0, locked_until=None)
    with patch("app.routes.auth.db.session.commit"):
        for _ in range(5):
            register_failed_login(account, "failed_login_attempts", "locked_until")
    assert account.locked_until is not None
    assert account.failed_login_attempts == 0


def test_payment_validation_and_status_helpers():
    from app.routes.payment_workflow import account_status, decimal_money

    assert decimal_money("350.25").as_tuple().exponent == -2
    assert decimal_money("not-money") is None
    assert account_status(SimpleNamespace(current_balance=0, total_paid=100)) == "Paid"
    assert account_status(SimpleNamespace(current_balance=50, total_paid=100)) == "Partially Paid"
    assert account_status(SimpleNamespace(current_balance=50, total_paid=0)) == "Unpaid"
