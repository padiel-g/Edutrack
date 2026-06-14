import click
import os
import time
from flask import Flask, Response, g, jsonify, redirect, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import db, jwt, limiter, migrate
from app.models import *  # noqa: F401,F403
from app.routes import register_routes
from app.services.token_blocklist import is_token_revoked


METRICS_REGISTRY = CollectorRegistry()
REQUEST_COUNT = Counter(
    "edutrack_http_requests_total",
    "HTTP requests processed by EduTrack.",
    ["method", "endpoint", "status"],
    registry=METRICS_REGISTRY,
)
REQUEST_LATENCY = Histogram(
    "edutrack_http_request_duration_seconds",
    "EduTrack HTTP request latency.",
    ["method", "endpoint"],
    registry=METRICS_REGISTRY,
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    validate_production_config(app)

    from flask_cors import CORS

    if not app.config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS must contain at least one trusted frontend origin.")
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=False,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )
    if app.config["TRUST_PROXY"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    register_routes(app)
    register_account_commands(app)
    register_error_handlers(app)

    @app.before_request
    def start_request_metrics():
        g.request_started_at = time.perf_counter()

    @app.before_request
    def enforce_https():
        if (
            app.config["FORCE_HTTPS"]
            and request.headers.get("X-Forwarded-Proto", request.scheme) != "https"
            and request.path != "/api/health"
        ):
            return redirect(request.url.replace("http://", "https://", 1), code=308)

    @app.before_request
    def enforce_temporary_password_change():
        allowed = {"/api/auth/me", "/api/auth/change-password", "/api/auth/logout", "/api/health"}
        if request.path in allowed or request.method == "OPTIONS" or not request.path.startswith("/api/"):
            return None
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt()
            identity = get_jwt_identity()
        except Exception:
            return None
        if not identity:
            return None
        if claims.get("mustChangePassword"):
            return jsonify(
                {
                    "error": "Password change required",
                    "message": "You must change your temporary password before continuing.",
                    "status": 403,
                }
            ), 403
        return None

    @jwt.token_in_blocklist_loader
    def token_in_blocklist(_header, payload):
        if is_token_revoked(payload.get("jti")):
            return True
        # Tokens issued by the hardened login flow always carry tokenVersion.
        # Keeping legacy tokens readable supports a rolling deployment; rotate
        # JWT_SECRET_KEY at deployment time to invalidate pre-upgrade tokens.
        if "tokenVersion" not in payload:
            return False
        identity = payload.get("sub")
        role = payload.get("role")
        token_version = int(payload.get("tokenVersion", 0))
        if role == "Parent":
            student = db.session.get(Student, payload.get("studentId"))
            return not student or token_version != int(getattr(student, "parent_token_version", 0) or 0)
        if not identity or not str(identity).isdigit():
            return True
        user = db.session.get(User, int(identity))
        return not user or token_version != int(getattr(user, "token_version", 0) or 0)

    @app.after_request
    def security_headers(response):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        duration = time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())
        REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, endpoint).observe(max(duration, 0))
        return response

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Unauthorized", "message": reason, "status": 401}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token", "message": reason, "status": 422}), 422

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify({"error": "Token expired", "message": "Sign in again.", "status": 401}), 401

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return jsonify({"error": "Token revoked", "message": "Sign in again.", "status": 401}), 401

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "EduTrack API", "database": "PostgreSQL"})

    @app.get("/api/ready")
    def ready():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            app.logger.exception("Readiness database check failed")
            return jsonify({"status": "not ready", "database": "unavailable"}), 503
        return jsonify({"status": "ready", "database": "PostgreSQL"})

    @app.get("/api/metrics")
    def metrics():
        return Response(generate_latest(METRICS_REGISTRY), content_type=CONTENT_TYPE_LATEST)

    register_schema_check(app)
    return app


def validate_production_config(app: Flask) -> None:
    if app.config.get("TESTING") or app.config.get("ENV") != "production":
        return
    rate_storage = (app.config.get("RATELIMIT_STORAGE_URI") or "").strip()
    if not rate_storage or rate_storage.startswith("memory://"):
        raise RuntimeError("RATELIMIT_STORAGE_URI must use shared storage such as Redis in production.")
    blocklist_storage = (app.config.get("JWT_BLOCKLIST_STORAGE_URI") or "").strip()
    if not blocklist_storage or blocklist_storage.startswith("memory://"):
        raise RuntimeError("JWT_BLOCKLIST_STORAGE_URI must use shared storage such as Redis in production.")
    required = [
        "CORS_ORIGINS", "RATELIMIT_STORAGE_URI", "FORCE_HTTPS", "TRUST_PROXY",
        "DB_POOL_SIZE", "DB_MAX_OVERFLOW", "DB_POOL_TIMEOUT", "DB_POOL_RECYCLE",
        "MATERIAL_UPLOAD_PATH", "BACKUP_PATH", "SMTP_HOST", "SMTP_PORT",
        "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL",
    ]
    missing = [name for name in required if not (os.getenv(name) or "").strip()]
    if missing:
        app.logger.warning("Missing production environment variables: %s", ", ".join(missing))


def register_schema_check(app: Flask) -> None:
    """Report an actionable error without blocking Flask-Migrate commands."""
    if not app.config.get("CHECK_DATABASE_SCHEMA", True):
        return

    schema_state = {"ready": False}

    @app.before_request
    def ensure_database_schema():
        if not schema_state["ready"]:
            inspector = inspect(db.engine)
            if inspector.has_table("announcements"):
                columns = {column["name"] for column in inspector.get_columns("announcements")}
                required = {"target_id", "video_path", "video_filename", "video_mime_type"}
                missing = sorted(required - columns)
                if missing:
                    message = (
                        "PostgreSQL schema is behind the SQLAlchemy models. "
                        f"Missing announcements columns: {', '.join(missing)}. "
                        'Run "flask db upgrade" with the configured DATABASE_URL.'
                    )
                    return jsonify(
                        {
                            "error": "Database migration required",
                            "message": message,
                            "status": 503,
                        }
                    ), 503
            schema_state["ready"] = True
        return None


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return jsonify({"error": error.name, "message": error.description, "status": error.code}), error.code

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        app.logger.warning("Database integrity error: %s", error)
        return jsonify({"error": "Conflict", "message": "The request conflicts with an existing record.", "status": 409}), 409

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled application error")
        return jsonify({"error": "Internal Server Error", "message": "The request could not be completed.", "status": 500}), 500


def register_account_commands(app: Flask) -> None:
    @app.cli.command("list-accounts")
    def list_accounts():
        """List accounts stored in PostgreSQL."""
        from app.models import User

        users = User.query.order_by(User.email).all()
        if not users:
            click.echo("No accounts found.")
            return

        for user in users:
            role = user.role.name if user.role else "No role"
            status = "active" if user.is_active else "disabled"
            click.echo(f"{user.email} | {role} | {status}")

    @app.cli.command("reset-password")
    @click.option("--email", prompt=True, help="Account email address.")
    @click.password_option(confirmation_prompt=True)
    def reset_password(email: str, password: str):
        """Securely reset an account password."""
        from app.models import User

        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            raise click.ClickException("No account exists with that email address.")
        if len(password) < 10:
            raise click.ClickException("Password must contain at least 10 characters.")

        user.set_password(password)
        db.session.commit()
        click.echo(f"Password reset for {user.email}.")

    @app.cli.command("delete-account")
    @click.option("--email", prompt=True, help="Account email address.")
    @click.option("--yes", is_flag=True, help="Skip the confirmation prompt.")
    def delete_account(email: str, yes: bool):
        """Delete an unlinked account from PostgreSQL."""
        from sqlalchemy.exc import IntegrityError

        from app.models import Parent, Student, Teacher, User

        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            raise click.ClickException("No account exists with that email address.")

        links = []
        if Student.query.filter_by(user_id=user.id).first():
            links.append("student")
        if Teacher.query.filter_by(user_id=user.id).first():
            links.append("teacher")
        if Parent.query.filter_by(user_id=user.id).first():
            links.append("parent")
        if links:
            linked = ", ".join(links)
            raise click.ClickException(
                f"Account is linked to a {linked} record. Remove or reassign that record first."
            )

        if not yes and not click.confirm(f"Delete account {user.email}?"):
            click.echo("Account deletion cancelled.")
            return

        try:
            db.session.delete(user)
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise click.ClickException(
                "Account is referenced by other records and cannot be deleted."
            ) from exc

        click.echo(f"Deleted account {user.email}.")
