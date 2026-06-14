from flask_jwt_extended import get_jwt_identity

from app.extensions import db
from app.models import AuditLog


def write_audit(action, entity_type, entity_id=None, details=None):
    try:
        user_id = int(get_jwt_identity() or 0) or None
    except Exception:
        user_id = None
    db.session.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}))
