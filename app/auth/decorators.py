from functools import wraps
from flask import session, request, redirect, url_for, jsonify, render_template
import logging
from app.firebase_db import audit_logs_col, get_db
from api_utils import api_error, permission_denied, log_audit_denied

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"ok": False, "message": "Authentication required."}), 401
            return redirect(url_for('auth.login_view', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator for role-gated routes.
    Checks session['user_role'] and session['staff_role'].
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_email = session.get('user_email')
            user_role = session.get('user_role', 'guest')
            staff_role = session.get('staff_role')

            if not user_email:
                if request.path.startswith('/api/'):
                    return jsonify({"ok": False, "message": "Authentication required."}), 401
                return redirect(url_for('auth.login_view', next=request.path))

            # Check if role or staff_role matches
            has_role = (user_role in allowed_roles) or (staff_role and staff_role in allowed_roles) or ('admin' in allowed_roles and user_role in ['admin', 'super_admin'])
            
            if not has_role:
                try:
                    db = get_db()
                    log_audit_denied(db, actor_id=user_email, actor_role=user_role, target=request.path, details=f"Required roles: {allowed_roles}")
                except Exception as e:
                    logger.error(f"Audit log failed: {e}")

                if request.path.startswith('/api/'):
                    return permission_denied(target=request.path, db=get_db())
                return render_template('permission_denied.html', 
                                       message=f"Access restricted to roles: {', '.join(allowed_roles)}.",
                                       user_role=user_role), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
