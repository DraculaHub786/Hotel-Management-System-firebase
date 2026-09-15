import time
import logging
from datetime import datetime, timedelta
import bcrypt
import hashlib
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import users_col, invites_col, password_resets_col, audit_logs_col
from app.auth.otp_service import generate_and_store_otp, verify_otp
from api_utils import api_success, api_error

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# Password hashing & verification
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        if hashed.startswith(('$2b$', '$2a$', '$2y$')):
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        sha_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if sha_hash.lower() == hashed.lower():
            return True
        if password == hashed:
            return True
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def is_valid_password(password: str) -> bool:
    return len(password) >= 8

def is_valid_staff_password(password: str) -> bool:
    if len(password) < 10:
        return False
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    return has_digit and has_symbol

# Rate limiting
failed_login_attempts = {}

def check_login_rate_limit(key: str):
    now = time.time()
    attempts = failed_login_attempts.get(key, [])
    valid_attempts = [t for t in attempts if now - t < 600]
    failed_login_attempts[key] = valid_attempts
    
    if len(valid_attempts) >= 5:
        oldest = valid_attempts[0]
        remaining_seconds = 600 - (now - oldest)
        minutes = max(1, int(remaining_seconds // 60) + 1)
        return True, minutes
    return False, 0

def record_failed_login(key: str):
    now = time.time()
    if key not in failed_login_attempts:
        failed_login_attempts[key] = []
    failed_login_attempts[key].append(now)

def clear_failed_login(key: str):
    failed_login_attempts.pop(key, None)

def get_role_redirect(role: str) -> str:
    r = (role or 'guest').lower()
    redirect_map = {
        'admin': '/admin',
        'super_admin': '/super-admin',
        'manager': '/manager',
        'front_desk': '/staff/front-desk',
        'housekeeping': '/staff/housekeeping',
        'laundry': '/staff/laundry',
        'room_service': '/staff/room-service',
        'waiter': '/dining/tables',
        'kitchen': '/staff/kitchen',
        'chef': '/staff/kitchen',
        'security': '/staff/security',
        'maintenance': '/staff/maintenance',
        'concierge': '/staff/concierge',
        'accountant': '/accounts'
    }
    return redirect_map.get(r, '/dashboard')

# Routes
@auth_bp.route('/login', methods=['GET'])
def login_view():
    if 'user_email' in session:
        return redirect(get_role_redirect(session.get('user_role', 'guest')))
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET'])
@auth_bp.route('/register', methods=['GET'])
def register_view():
    if 'user_email' in session:
        return redirect(get_role_redirect(session.get('user_role', 'guest')))
    return render_template('signup.html')

@auth_bp.route('/api/auth/register', methods=['POST'])
@auth_bp.route('/api/register', methods=['POST'])
@auth_bp.route('/api/auth/signup', methods=['POST'])
def register_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    role = data.get('role', 'guest')
    otp_code = data.get('otp', '').strip()

    if not email or not password or not name:
        return api_error(message="Name, email, and password are required.", status=400)

    if not is_valid_password(password):
        return api_error(errors={'password': 'Password must be at least 8 characters long.'}, message="Weak password.", status=422)

    col = users_col()
    existing = list(col.where('email', '==', email).limit(1).get())
    if existing:
        return api_error(message="User with this email already exists.", status=409)

    # If OTP is not provided, generate OTP and return request
    if not otp_code:
        code = generate_and_store_otp(email, purpose='register')
        return api_success({
            "requires_otp": True,
            "email": email,
            "message": "OTP has been generated and sent to your email.",
            "dev_otp": code # included for testing convenience
        })

    # Verify OTP
    ok, msg = verify_otp(email, otp_code, purpose='register')
    if not ok:
        return api_error(message=msg, status=400)

    # Create User
    new_user = {
        "email": email,
        "name": name,
        "phone": phone,
        "password": hash_password(password),
        "role": role if role in ['member', 'guest', 'user'] else 'guest',
        "staff_role": None,
        "is_active": True,
        "discount_percent": 5.0 if role == 'member' else 0.0,
        "loyalty_points": 50 if role == 'member' else 0,
        "google_auth": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    col.add(new_user)
    
    session['user_email'] = email
    session['user_name'] = name
    session['user_role'] = new_user['role']
    session.permanent = True

    return api_success({
        "message": "Registration successful!",
        "redirect_url": get_role_redirect(new_user['role'])
    })

@auth_bp.route('/api/auth/login', methods=['POST'])
@auth_bp.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return api_error(message="Email and password are required.", status=400)

    rate_key = f"{request.remote_addr}:{email}"
    is_blocked, wait_mins = check_login_rate_limit(rate_key)
    if is_blocked:
        return api_error(message=f"Too many failed login attempts. Please wait {wait_mins} minute(s).", status=429)

    col = users_col()
    docs = list(col.where('email', '==', email).limit(1).get())
    if not docs:
        record_failed_login(rate_key)
        return api_error(message="Invalid email or password.", status=401)

    user_doc = docs[0]
    user_data = user_doc.to_dict()

    if not user_data.get('is_active', True):
        return api_error(message="This account has been deactivated. Please contact support.", status=403)

    stored_hash = user_data.get('password', '')
    if not verify_password(password, stored_hash):
        record_failed_login(rate_key)
        return api_error(message="Invalid email or password.", status=401)

    clear_failed_login(rate_key)

    session['user_email'] = email
    session['user_name'] = user_data.get('name', email.split('@')[0])
    session['user_role'] = user_data.get('role', 'guest')
    session['staff_role'] = user_data.get('staff_role')
    session['property_id'] = user_data.get('property_id', 'prop_1')
    session.permanent = True

    return api_success({
        "message": "Login successful!",
        "user": {
            "email": email,
            "name": session['user_name'],
            "role": session['user_role']
        },
        "redirect_url": get_role_redirect(session['user_role'])
    })

@auth_bp.route('/api/auth/verify-otp', methods=['POST'])
@auth_bp.route('/api/otp/verify', methods=['POST'])
def verify_otp_endpoint():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    code = data.get('otp', data.get('code', '')).strip()
    purpose = data.get('purpose', 'register')

    if not email or not code:
        return api_error(message="Email and OTP code are required.", status=400)

    ok, msg = verify_otp(email, code, purpose=purpose)
    if not ok:
        return api_error(message=msg, status=400)
    return api_success({"message": msg})

@auth_bp.route('/api/auth/resend-otp', methods=['POST'])
def resend_otp_endpoint():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    purpose = data.get('purpose', 'register')

    if not email:
        return api_error(message="Email is required.", status=400)

    code = generate_and_store_otp(email, purpose=purpose)
    return api_success({
        "message": "A new OTP code has been generated.",
        "dev_otp": code
    })

@auth_bp.route('/api/google-auth', methods=['POST'])
@auth_bp.route('/api/auth/google', methods=['POST'])
def google_auth_api():
    data = request.get_json() or {}
    credential = data.get('credential')
    email = data.get('email')
    
    if not credential and not email:
        return api_error(message="Invalid Google authentication data", status=400)
        
    user_email = email or data.get('user_email', 'google_user@gmail.com')
    user_name = data.get('name', user_email.split('@')[0])

    col = users_col()
    docs = list(col.where('email', '==', user_email).limit(1).get())
    if not docs:
        new_user = {
            "email": user_email,
            "name": user_name,
            "role": "guest",
            "google_auth": True,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        col.add(new_user)
        role = "guest"
    else:
        role = docs[0].to_dict().get('role', 'guest')

    session['user_email'] = user_email
    session['user_name'] = user_name
    session['user_role'] = role
    session.permanent = True

    return api_success({
        "message": "Google authentication successful",
        "redirect_url": get_role_redirect(role)
    })

@auth_bp.route('/logout', methods=['GET', 'POST'])
@auth_bp.route('/signout', methods=['GET', 'POST'])
@auth_bp.route('/api/auth/logout', methods=['POST'])
@auth_bp.route('/api/logout', methods=['POST'])
def logout_api():
    session.clear()
    if request.path.startswith('/api/'):
        return api_success({"message": "Logged out successfully", "redirect_url": "/login"})
    return redirect(url_for('auth.login_view'))

@auth_bp.route('/forgot-password', methods=['GET'])
def forgot_password_view():
    return render_template('forgot_password.html')

@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
@auth_bp.route('/api/auth/forgot', methods=['POST'])
def forgot_password_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    if not email:
        return api_error(message="Email is required.", status=400)
    
    code = generate_and_store_otp(email, purpose='reset')
    return api_success({
        "message": "Password reset code sent to your email.",
        "dev_otp": code
    })

@auth_bp.route('/reset-password/<token>', methods=['GET'])
@auth_bp.route('/reset-password', methods=['GET'])
def reset_password_view(token=None):
    return render_template('reset_password.html', token=token)

@auth_bp.route('/api/auth/reset-password', methods=['POST'])
@auth_bp.route('/api/auth/reset', methods=['POST'])
def reset_password_api():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', data.get('token', '')).strip()
    new_password = data.get('new_password', data.get('password', ''))

    if not email or not otp_code or not new_password:
        return api_error(message="Email, reset code, and new password are required.", status=400)

    if not is_valid_password(new_password):
        return api_error(message="Password must be at least 8 characters long.", status=422)

    ok, msg = verify_otp(email, otp_code, purpose='reset')
    if not ok:
        return api_error(message=msg, status=400)

    col = users_col()
    docs = list(col.where('email', '==', email).limit(1).get())
    if not docs:
        return api_error(message="User not found.", status=404)

    docs[0].reference.update({"password": hash_password(new_password)})
    return api_success({"message": "Password reset successfully! You may now sign in."})

def init_seed_users():
    """Initializes standard seed accounts per master_plan with Hotel@123 password"""
    seeds = [
        {"email": "admin@nur-e-haya.com", "name": "System Administrator", "role": "admin", "staff_role": None},
        {"email": "test1@gmail.com", "name": "Admin Tester", "role": "admin", "staff_role": None},
        {"email": "manager@nur-e-haya.com", "name": "General Manager", "role": "manager", "staff_role": None},
        {"email": "chef@nur-e-haya.com", "name": "Head Chef", "role": "chef", "staff_role": "chef"},
        {"email": "frontdesk@nur-e-haya.com", "name": "Front Desk Officer", "role": "front_desk", "staff_role": "front_desk"},
        {"email": "cleaning@nur-e-haya.com", "name": "Housekeeping Lead", "role": "housekeeping", "staff_role": "housekeeping"},
        {"email": "laundry@nur-e-haya.com", "name": "Laundry Specialist", "role": "laundry", "staff_role": "laundry"},
        {"email": "maintenance@nur-e-haya.com", "name": "Chief Engineer", "role": "maintenance", "staff_role": "maintenance"},
        {"email": "concierge@nur-e-haya.com", "name": "Chief Concierge", "role": "concierge", "staff_role": "concierge"},
        {"email": "accountant@nur-e-haya.com", "name": "Senior Accountant", "role": "accountant", "staff_role": None},
        {"email": "member@nur-e-haya.com", "name": "VIP Club Member", "role": "member", "staff_role": None, "discount_percent": 5.0},
        {"email": "user@nur-e-haya.com", "name": "Guest Traveler", "role": "guest", "staff_role": None}
    ]
    col = users_col()
    pw_hash = hash_password("Hotel@123")
    now_str = datetime.utcnow().isoformat() + "Z"

    for s in seeds:
        try:
            q = list(col.where('email', '==', s['email']).limit(1).get())
            if not q:
                user_doc = {
                    "email": s['email'],
                    "name": s['name'],
                    "password": pw_hash,
                    "role": s['role'],
                    "staff_role": s.get('staff_role'),
                    "property_id": "prop_1",
                    "created_at": now_str,
                    "google_auth": False,
                    "is_active": True,
                    "discount_percent": s.get('discount_percent', 0.0),
                    "loyalty_points": 100 if s['role'] == 'member' else 0
                }
                col.add(user_doc)
                logger.info(f"🌱 Seeded user: {s['email']} ({s['role']})")
            else:
                doc = q[0]
                doc.reference.update({
                    "name": s['name'],
                    "role": s['role'],
                    "staff_role": s.get('staff_role'),
                    "is_active": True
                })
        except Exception as e:
            logger.warning(f"Seed user error for {s['email']}: {e}")
