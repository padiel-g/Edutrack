from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token


def teacher_headers(app):
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "Teacher", "permissions": [], "mustChangePassword": False},
        )
    return {"Authorization": f"Bearer {token}"}


def test_teacher_login_succeeds(client):
    user = MagicMock()
    user.id = 7
    user.email = "teacher@example.com"
    user.is_active = True
    user.status = "Active"
    user.must_change_password = False
    user.role.name = "Teacher"
    user.role.permissions = []
    user.check_password.return_value = True
    user.to_dict.return_value = {"id": 7, "role": "Teacher"}

    with (
        patch("app.routes.auth.User.query") as query,
        patch("app.routes.auth.write_audit"),
        patch("app.routes.auth.db.session.commit"),
    ):
        query.filter_by.return_value.first.return_value = user
        response = client.post(
            "/api/auth/login",
            json={"email": user.email, "password": "correct-password", "role": "Teacher"},
        )

    assert response.status_code == 200
    assert response.get_json()["redirectPath"] == "/teacher"


def test_teacher_announcements_returns_empty_json(client, app):
    empty_query = MagicMock()
    empty_query.all.return_value = []
    current_user = SimpleNamespace(must_change_password=False)
    with (
        patch("app.routes.announcements.visible_announcements", return_value=empty_query),
        patch("app.db.session.get", return_value=current_user),
    ):
        response = client.get("/api/announcements", headers=teacher_headers(app))

    assert response.status_code == 200
    assert response.get_json() == {"items": [], "total": 0}


def test_teacher_analytics_returns_valid_json(client, app):
    count_query = MagicMock()
    count_query.count.return_value = 0
    count_query.filter_by.return_value.count.return_value = 0
    scalar_query = MagicMock()
    scalar_query.scalar.return_value = 0
    announcements = MagicMock()
    announcements.limit.return_value = []
    current_user = SimpleNamespace(must_change_password=False)

    with (
        patch("app.routes.analytics.Attendance.query", count_query),
        patch("app.routes.analytics.db.session.query", return_value=scalar_query),
        patch("app.routes.analytics.Student.query.count", return_value=0),
        patch("app.routes.analytics.Teacher.query.count", return_value=0),
        patch("app.routes.analytics.Parent.query.count", return_value=0),
        patch("app.routes.analytics.SchoolClass.query.count", return_value=0),
        patch("app.routes.analytics.AuditLog.query") as audit_query,
        patch("app.routes.analytics.visible_announcements", return_value=announcements),
        patch("app.db.session.get", return_value=current_user),
    ):
        audit_query.order_by.return_value.limit.return_value = []
        response = client.get("/api/dashboard/analytics", headers=teacher_headers(app))

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["recentAnnouncements"] == []
    assert payload["attendance"]["presentRate"] == 0


def test_parent_announcement_filter_keeps_specific_recipient_private(app):
    from flask_jwt_extended import create_access_token

    from app.routes.announcements import visible_query

    with app.test_request_context():
        token = create_access_token(
            identity="parent:3",
            additional_claims={"role": "Parent", "permissions": [], "studentId": 3},
        )

    with (
        app.test_request_context(headers={"Authorization": f"Bearer {token}"}),
        patch("app.routes.announcements.Announcement.query") as query,
        patch("app.routes.announcements.verify_jwt_in_request", create=True),
    ):
        from flask_jwt_extended import verify_jwt_in_request

        verify_jwt_in_request()
        visible_query()

    expression = str(query.filter.call_args.args[0])
    assert "announcements.audience IN" in expression
    assert "announcements.target_id" in expression
    assert "announcements.audience = " in expression


def test_accounts_officer_role_is_created_when_missing(client, app):
    admin = SimpleNamespace(must_change_password=False, token_version=0)
    created_role = SimpleNamespace(id=6, name="Accounts Officer", permissions=[])

    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "Admin", "permissions": [], "mustChangePassword": False},
        )

    with (
        patch("app.routes.auth.Role", return_value=created_role) as role_model,
        patch("app.routes.auth.User") as user_model,
        patch("app.routes.auth.db.session.add"),
        patch("app.routes.auth.db.session.flush"),
        patch("app.routes.auth.db.session.commit"),
        patch("app.routes.auth.write_audit"),
        patch("app.db.session.get", return_value=admin),
    ):
        user_model.query.filter_by.return_value.first.return_value = None
        role_model.query.filter_by.return_value.first.return_value = None
        user = user_model.return_value
        user.id = 12
        user.to_dict.return_value = {"id": 12, "role": "Accounts Officer"}
        response = client.post(
            "/api/auth/accounts",
            headers={"Authorization": f"Bearer {token}"},
            json={"firstName": "Ava", "lastName": "Moyo", "email": "accounts@example.com"},
        )

    assert response.status_code == 201
    role_model.assert_called_once()
    temporary_password = response.get_json()["temporaryPassword"]
    assert temporary_password != "Edutrack"
    user.set_password.assert_called_once_with(temporary_password)
    assert user_model.call_args.kwargs["must_change_password"] is True
