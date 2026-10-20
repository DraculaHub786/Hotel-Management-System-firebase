import os
import sys
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig
from app.firebase_db import get_db

# CRITICAL protobuf setting
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            config_class = ProductionConfig
        elif env == 'testing':
            config_class = TestingConfig
        else:
            config_class = DevelopmentConfig
    elif isinstance(config_class, str):
        config_map = {
            'production': ProductionConfig,
            'testing': TestingConfig,
            'development': DevelopmentConfig
        }
        config_class = config_map.get(config_class.lower(), DevelopmentConfig)

    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    # Configure restricted CORS per Security Fix 5
    raw_origins = os.getenv('ALLOWED_ORIGINS', '')
    allowed_origins = [o.strip() for o in raw_origins.split(',') if o.strip()]
    if not allowed_origins:
        allowed_origins = ['http://localhost:5000', 'http://127.0.0.1:5000', 'https://nur-e-haya.onrender.com']
    CORS(app, origins=allowed_origins if os.getenv('FLASK_ENV') == 'production' else '*', supports_credentials=True)

    # CSRF Protection per Security Fix 4
    import secrets
    def get_or_create_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(24)
        return session['_csrf_token']

    app.jinja_env.globals['csrf_token'] = get_or_create_csrf_token

    @app.before_request
    def validate_csrf():
        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return
        if app.config.get('TESTING'):
            return
        if request.path.startswith(('/api/auth/invite/accept', '/api/invite/', '/api/login', '/api/register', '/api/google-auth', '/api/auth/google')):
            return
        if session.get('user_email') and '_csrf_token' in session:
            token = request.headers.get('X-CSRF-Token')
            if not token and request.form:
                token = request.form.get('csrf_token')
            if not token and request.is_json:
                data = request.get_json(silent=True) or {}
                token = data.get('csrf_token')
            if not token or token != session['_csrf_token']:
                if request.path.startswith('/api/'):
                    return jsonify({"ok": False, "message": "Invalid or missing CSRF token."}), 403
                return render_template('permission_denied.html', message="Invalid or missing CSRF token.", user_role=session.get('user_role', 'guest')), 403

    # Initialize Firestore
    db = get_db()

    # Register Blueprints
    from app.auth.routes import auth_bp, init_seed_users
    from app.core.routes import core_bp
    from app.frontdesk.routes import frontdesk_bp
    from app.dining.routes import dining_bp
    from app.services.routes import services_bp
    from app.maintenance.routes import maintenance_bp
    from app.concierge.routes import concierge_bp
    from app.payments.routes import payments_bp
    from app.events.routes import events_bp
    from app.security.routes import security_bp
    from app.manager.routes import manager_bp
    from app.admin.routes import admin_bp
    from app.crm.routes import crm_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(frontdesk_bp)
    app.register_blueprint(dining_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(concierge_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(security_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(crm_bp)

    # Initialize seeds
    try:
        init_seed_users()
    except Exception as e:
        logger.warning(f"Initial seed execution deferred: {e}")

    # Root route
    @app.route('/')
    def index():
        if 'user_email' in session:
            from app.auth.routes import get_role_redirect
            return redirect(get_role_redirect(session.get('user_role', 'guest')))
        return redirect('/login')

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"ok": True, "status": "healthy", "service": "nur-e-haya-os"})

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({"ok": False, "message": "You do not have permission to perform this action."}), 403
        return render_template('permission_denied.html', message="Forbidden: Access Denied", user_role=session.get('user_role', 'guest')), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"ok": False, "message": "Resource not found."}), 404
        return render_template('permission_denied.html', message="Page Not Found", user_role=session.get('user_role', 'guest')), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal server error: {e}")
        if request.path.startswith('/api/'):
            return jsonify({"ok": False, "message": "Internal server error occurred."}), 500
        return render_template('permission_denied.html', message="Internal Server Error", user_role=session.get('user_role', 'guest')), 500

    return app

# Instantiate top-level application instance for `from app import app`
app = create_app()

# Re-export legacy symbols needed by unit tests
from app.auth.routes import (
    is_valid_password,
    is_valid_staff_password,
    check_login_rate_limit,
    record_failed_login,
    clear_failed_login,
    get_role_redirect,
    hash_password,
    verify_password
)
