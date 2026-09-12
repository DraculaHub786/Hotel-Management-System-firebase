"""
api_utils.py - Shared API and UI conventions helper functions
Adheres strictly to todo.md Section A (A.4 API envelope, A.5 Permission-denied, audit logging)
"""

from flask import jsonify, session, request
from datetime import datetime
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def api_success(data=None, status=200):
    """
    Standard success envelope:
    { "ok": true, "data": { ... } }
    """
    return jsonify({
        "ok": True,
        "data": data if data is not None else {}
    }), status

def api_error(errors=None, message="An error occurred", status=400):
    """
    Standard error envelope:
    { "ok": false, "errors": { "field_name": "Human readable message" }, "message": "Optional top-level message" }
    """
    response_body = {
        "ok": False,
        "errors": errors if errors is not None else {},
        "message": message
    }
    return jsonify(response_body), status

def log_audit_denied(db, actor_id=None, actor_role=None, target=None, details=None):
    """
    Log unauthorized/denied access attempt to Firestore audit_logs collection per Section A.1 & A.5
    """
    try:
        if db is not None:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "actor_id": actor_id or session.get("user_email") or "anonymous",
                "actor_role": actor_role or session.get("user_role") or "guest",
                "action": "denied_access_attempt",
                "target_type": "screen_or_endpoint",
                "target_id": target or request.path,
                "ip_address": request.remote_addr,
                "details": details or f"Unauthorized attempt on {request.path}"
            }
            db.collection("audit_logs").add(audit_entry)
            logger.warning(f"🔒 Denied access logged to audit_logs: {audit_entry}")
    except Exception as e:
        logger.error(f"Failed to write to audit_logs: {str(e)}")

def permission_denied(message="You do not have permission to perform this action.", target=None, db=None):
    """
    Standard HTTP 403 response per Section A.5:
    { "ok": false, "message": "You do not have permission to perform this action." }
    """
    if db is not None:
        log_audit_denied(db, target=target)
    return jsonify({
        "ok": False,
        "message": message
    }), 403

def role_required(*allowed_roles, db=None):
    """
    Decorator for role-gated routes.
    If unauthorized, logs to audit_logs and returns standard 403 or redirects.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_email = session.get("user_email")
            user_role = session.get("user_role", "guest")

            if not user_email:
                if request.path.startswith("/api/"):
                    return jsonify({
                        "ok": False,
                        "message": "Authentication required."
                    }), 401
                from flask import redirect, url_for
                return redirect(url_for('login'))


            if allowed_roles and user_role not in allowed_roles:
                target_route = request.path
                if db is not None:
                    log_audit_denied(db, actor_id=user_email, actor_role=user_role, target=target_route)
                
                if request.path.startswith("/api/"):
                    return permission_denied(target=target_route, db=db)
                else:
                    # Render standard permission-denied template or return 403
                    from flask import render_template
                    return render_template("permission_denied.html", 
                                           message="You do not have permission to perform this action.",
                                           return_url="/dashboard"), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
