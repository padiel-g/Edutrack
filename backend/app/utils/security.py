from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles and claims.get("role") != "Super Admin":
                return jsonify({"error": "Forbidden", "requiredRoles": roles}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def permissions_required(*permissions):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            granted = set(claims.get("permissions", []))
            if not set(permissions).issubset(granted) and claims.get("role") != "Super Admin":
                return jsonify({"error": "Forbidden", "requiredPermissions": permissions}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
