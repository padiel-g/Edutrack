import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.models import PasswordResetCode, Role, Student, Teacher, User
from app.services.audit import write_audit
from app.services.email import send_password_reset_code
from app.services.token_blocklist import revoke_token
from app.utils.credentials import generate_temporary_password, is_strong_password
from app.utils.security import roles_required

auth_bp = Blueprint("auth", __name__)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def strong_password(password):
    return is_strong_password(password)


def account_locked(locked_until):
    return isinstance(locked_until, datetime) and locked_until > datetime.utcnow()


def register_failed_login(account, attempts_field, locked_field):
    attempts = int(getattr(account, attempts_field, 0) or 0) + 1
    setattr(account, attempts_field, attempts)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        setattr(account, locked_field, datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES))
        setattr(account, attempts_field, 0)
    db.session.commit()


def clear_failed_logins(account, attempts_field, locked_field):
    setattr(account, attempts_field, 0)
    setattr(account, locked_field, None)


def user_claims(user):
    return {
        "role": user.role.name,
        "permissions": [p.name for p in user.role.permissions],
        "mustChangePassword": user.must_change_password,
        "tokenVersion": int(getattr(user, "token_version", 0) or 0),
    }


def parent_claims(student):
    return {
        "role": "Parent",
        "permissions": [],
        "studentId": student.id,
        "mustChangePassword": student.parent_must_change_password,
        "tokenVersion": int(getattr(student, "parent_token_version", 0) or 0),
    }


def revoke_current_token():
    claims = get_jwt()
    revoke_token(claims.get("jti"), claims.get("exp"))


@auth_bp.post("/forgot-password/request")
@limiter.limit("3 per 15 minutes")
def request_password_reset():
    email = ((request.get_json() or {}).get("email") or "").strip().lower()
    generic = "If an active teacher account matches that email, a verification code will be sent by email."
    user = User.query.filter_by(email=email).first()
    teacher = Teacher.query.filter_by(user_id=user.id).first() if user and user.role and user.role.name == "Teacher" else None
    if not user or not teacher or user.status != "Active" or not user.is_active:
        current_app.logger.info(
            "Teacher password reset skipped for %s: user=%s role=%s teacher=%s status=%s active=%s",
            email or "<empty>",
            bool(user),
            user.role.name if user and user.role else None,
            bool(teacher),
            user.status if user else None,
            user.is_active if user else None,
        )
        return jsonify({"message": generic}), 200

    now = datetime.utcnow()
    PasswordResetCode.query.filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used_at.is_(None),
    ).update({"used_at": now})
    code = f"{secrets.randbelow(1000000):06d}"
    reset = PasswordResetCode(
        user_id=user.id,
        code_hash=generate_password_hash(code),
        expires_at=now + timedelta(minutes=10),
    )
    db.session.add(reset)
    db.session.flush()
    write_audit("teacher_reset_requested", "User", user.id, {"delivery": "Email"})
    db.session.commit()
    try:
        send_password_reset_code(user.email, code)
    except RuntimeError as error:
        reset.used_at = datetime.utcnow()
        db.session.commit()
        current_app.logger.exception("Teacher password reset email delivery failed.")
        return jsonify({"error": str(error)}), 503
    return jsonify({"message": generic}), 200


@auth_bp.post("/forgot-password/verify")
@limiter.limit("8 per 15 minutes")
def verify_password_reset():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    user = User.query.filter_by(email=email).first()
    reset = (
        PasswordResetCode.query.filter_by(user_id=user.id, used_at=None)
        .order_by(PasswordResetCode.id.desc())
        .first()
        if user and user.role and user.role.name == "Teacher"
        else None
    )
    now = datetime.utcnow()
    if not reset or reset.expires_at < now or reset.attempts >= 5:
        return jsonify({"error": "Invalid or expired verification code."}), 400
    reset.attempts += 1
    if not check_password_hash(reset.code_hash, code):
        db.session.commit()
        return jsonify({"error": "Invalid or expired verification code."}), 400

    token = secrets.token_urlsafe(32)
    reset.reset_token_hash = generate_password_hash(token)
    reset.reset_token_expires_at = now + timedelta(minutes=10)
    reset.verified_at = now
    write_audit("teacher_reset_verified", "User", user.id)
    db.session.commit()
    return jsonify({"resetToken": token}), 200


@auth_bp.post("/forgot-password/reset")
@limiter.limit("5 per hour")
def complete_password_reset():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    token = data.get("resetToken") or ""
    new_password = data.get("newPassword") or ""
    confirm_password = data.get("confirmPassword") or ""
    if new_password != confirm_password:
        return jsonify({"error": "New password and confirmation do not match."}), 400
    if not strong_password(new_password):
        return jsonify({"error": "Password must be at least 10 characters and include uppercase, lowercase, number, and special character."}), 400

    user = User.query.filter_by(email=email).first()
    reset = (
        PasswordResetCode.query.filter_by(user_id=user.id, used_at=None)
        .filter(PasswordResetCode.verified_at.is_not(None))
        .order_by(PasswordResetCode.id.desc())
        .first()
        if user and user.role and user.role.name == "Teacher"
        else None
    )
    now = datetime.utcnow()
    if (
        not reset
        or not reset.reset_token_hash
        or not reset.reset_token_expires_at
        or reset.reset_token_expires_at < now
        or not check_password_hash(reset.reset_token_hash, token)
    ):
        return jsonify({"error": "Invalid or expired password reset session."}), 400

    user.set_password(new_password)
    user.must_change_password = False
    user.password_changed_at = now
    user.token_version += 1
    reset.used_at = now
    write_audit("teacher_password_reset", "User", user.id, {"delivery": "Email"})
    db.session.commit()
    return jsonify({"message": "Password reset successfully. You can now sign in."}), 200


@auth_bp.post("/register")
@jwt_required()
@roles_required("Admin", "Super Admin")
@limiter.limit("5 per hour")
def register():
    data = request.get_json() or {}
    role = Role.query.filter_by(name=data.get("role", "Student")).first()
    if not role:
        return jsonify({"error": "Invalid role"}), 400
    if User.query.filter_by(email=data.get("email")).first():
        return jsonify({"error": "Email already exists"}), 409
    if not strong_password(data.get("password") or ""):
        return jsonify({"error": "Password must be at least 10 characters and include uppercase, lowercase, number, and special character."}), 400
    user = User(
        email=data["email"],
        first_name=data.get("firstName", "New"),
        last_name=data.get("lastName", "User"),
        role=role,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()
    write_audit("user_registered", "User", user.id, {"email": user.email, "role": role.name})
    db.session.commit()
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.post("/accounts")
@jwt_required()
@roles_required("Admin", "Super Admin")
@limiter.limit("20 per hour")
def create_accounts_officer():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    if not email or not first_name or not last_name:
        return jsonify({"error": "First name, last name, and email are required."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists."}), 409
    role = Role.query.filter_by(name="Accounts Officer").first()
    if not role:
        role = Role(
            name="Accounts Officer",
            description="Manages student fees, invoices, payments, receipts, and finance reports.",
        )
        db.session.add(role)
        db.session.flush()

    temporary_password = generate_temporary_password()
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        must_change_password=True,
    )
    user.set_password(temporary_password)
    db.session.add(user)
    db.session.flush()
    write_audit("accounts_officer_created", "User", user.id, {"email": email})
    db.session.commit()
    return jsonify({
        "user": user.to_dict(),
        "defaultPassword": temporary_password,
        "temporaryPassword": temporary_password,
    }), 201


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    requested_role = data.get("role")
    if requested_role == "Parent":
        registration_number = (data.get("registrationNumber") or data.get("email") or "").strip()
        student = Student.query.filter_by(registration_number=registration_number).first()
        if not student:
            return jsonify({"error": "Invalid registration number or password"}), 401
        if account_locked(student.parent_locked_until):
            return jsonify({"error": "Account temporarily locked. Try again later."}), 423
        if not student.check_parent_password(data.get("password", "")):
            register_failed_login(student, "parent_failed_login_attempts", "parent_locked_until")
            return jsonify({"error": "Invalid registration number or password"}), 401
        if student.status != "active":
            return jsonify({"error": "Student account is inactive"}), 403
        clear_failed_logins(student, "parent_failed_login_attempts", "parent_locked_until")
        claims = parent_claims(student)
        token = create_access_token(identity=f"parent:{student.id}", additional_claims=claims)
        write_audit("parent_login", "Student", student.id, {"registrationNumber": student.registration_number})
        db.session.commit()
        return jsonify({
            "accessToken": token,
            "user": {
                "id": student.id,
                "email": student.registration_number,
                "firstName": "Parent of",
                "lastName": student.to_dict()["name"],
                "name": f"Parent of {student.to_dict()['name']}",
                "role": "Parent",
                "permissions": [],
                "mustChangePassword": student.parent_must_change_password,
            },
            "mustChangePassword": student.parent_must_change_password,
            "redirectPath": "/parent/change-password" if student.parent_must_change_password else "/parent",
        })

    user = User.query.filter_by(email=data.get("email")).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    if account_locked(user.locked_until):
        return jsonify({"error": "Account temporarily locked. Try again later."}), 423
    if not user.check_password(data.get("password", "")):
        register_failed_login(user, "failed_login_attempts", "locked_until")
        return jsonify({"error": "Invalid credentials"}), 401
    if not user.is_active or user.status != "Active":
        return jsonify({"error": f"Account is {user.status.lower()}"}), 403
    if requested_role and user.role and user.role.name != requested_role:
        return jsonify({"error": f"This account is registered as {user.role.name}, not {requested_role}."}), 403
    clear_failed_logins(user, "failed_login_attempts", "locked_until")
    claims = user_claims(user)
    token = create_access_token(identity=str(user.id), additional_claims=claims)
    user.last_login_at = datetime.utcnow()
    action = "teacher_login" if user.role.name == "Teacher" else "login"
    write_audit(action, "User", user.id, {"email": user.email})
    db.session.commit()
    redirect_path = "/change-password" if user.must_change_password else {
        "Teacher": "/teacher",
        "Admin": "/admin",
        "Super Admin": "/admin",
        "Student": "/student",
        "Accounts Officer": "/accounts",
    }.get(user.role.name, "/dashboard")
    return jsonify(
        {
            "accessToken": token,
            "user": user.to_dict(),
            "role": user.role.name,
            "mustChangePassword": user.must_change_password,
            "redirectPath": redirect_path,
        }
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    claims = get_jwt()
    if claims.get("role") == "Parent":
        student = db.session.get(Student, claims.get("studentId"))
        if not student:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"student": student.to_dict()})
    user = db.session.get(User, int(get_jwt_identity()))
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/change-password")
@jwt_required()
@limiter.limit("5 per hour")
def change_password():
    data = request.get_json() or {}
    current_password = data.get("currentPassword") or data.get("current_password") or ""
    new_password = data.get("newPassword") or data.get("new_password") or ""
    confirm_password = data.get("confirmPassword") or data.get("confirm_password") or ""
    if new_password != confirm_password:
        return jsonify({"error": "New password and confirmation do not match."}), 400
    if not strong_password(new_password):
        return jsonify({"error": "Password must be at least 10 characters and include uppercase, lowercase, number, and special character."}), 400

    claims = get_jwt()
    if claims.get("role") == "Parent":
        student = db.session.get(Student, claims.get("studentId"))
        if not student or not student.check_parent_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        student.set_parent_password(new_password)
        student.parent_must_change_password = False
        student.parent_token_version += 1
        write_audit("parent_password_changed", "Student", student.id)
        db.session.commit()
        revoke_current_token()
        token = create_access_token(identity=f"parent:{student.id}", additional_claims=parent_claims(student))
        return jsonify({
            "message": "Password changed successfully",
            "accessToken": token,
            "user": {
                "id": student.id,
                "email": student.registration_number,
                "firstName": "Parent of",
                "lastName": student.to_dict()["name"],
                "name": f"Parent of {student.to_dict()['name']}",
                "role": "Parent",
                "permissions": [],
                "mustChangePassword": False,
            },
        })
    else:
        user = db.session.get(User, int(get_jwt_identity()))
        if not user or not user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        user.set_password(new_password)
        user.must_change_password = False
        user.password_changed_at = datetime.utcnow()
        user.token_version += 1
        action = "teacher_password_changed" if user.role.name == "Teacher" else "password_changed"
        write_audit(action, "User", user.id)
    db.session.commit()
    revoke_current_token()
    token = create_access_token(identity=str(user.id), additional_claims=user_claims(user))
    return jsonify({"message": "Password changed successfully", "user": user.to_dict(), "accessToken": token})


@auth_bp.post("/logout")
@jwt_required()
@limiter.limit("30 per minute")
def logout():
    claims = get_jwt()
    action = "teacher_logout" if claims.get("role") == "Teacher" else "logout"
    write_audit(action, "User")
    db.session.commit()
    revoke_current_token()
    return jsonify({"message": "Logged out."})
