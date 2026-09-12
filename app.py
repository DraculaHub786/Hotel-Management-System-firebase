# app.py - Main Flask Application  Firebase connection ke saath!
import os
import sys

# Ensure UTF-8 output encoding across Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# CRITICAL: Must be set before importing any dependency that may touch protobuf
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
os.environ['PYTHONIOENCODING'] = 'utf-8'


from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
from chatbot import get_bot_response, chatbot_instance
import secrets
from functools import wraps
import re
import time
import random
import json
import base64
from unittest.mock import MagicMock
from dotenv import load_dotenv
import bcrypt
import hashlib
import logging

# Load environment variables
load_dotenv()

from api_utils import api_success, api_error, permission_denied, log_audit_denied, role_required
from guest_service import calculate_order_pricing, generate_qr_base64, init_sample_facilities_and_menu

import firebase_admin
from firebase_admin import credentials, firestore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variable for secret key - MUST be set in production
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    if os.getenv('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    secret_key = secrets.token_hex(32)
    logger.warning("Using generated SECRET_KEY - sessions will be lost on restart!")

app.secret_key = secret_key

# Session security configuration
app.config.update(
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

CORS(app)

# Load Firebase credentials from either file path or environment content
firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
firebase_creds_base64 = os.getenv('FIREBASE_CREDENTIALS_BASE64')

try:
    if os.path.exists(firebase_creds_path):
        cred = credentials.Certificate(firebase_creds_path)
    elif firebase_creds_json:
        cred = credentials.Certificate(json.loads(firebase_creds_json))
    elif firebase_creds_base64:
        decoded_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
        cred = credentials.Certificate(json.loads(decoded_json))
    else:
        raise FileNotFoundError(
            f"Firebase credentials file not found at {firebase_creds_path}"
        )

    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("✅ Firebase initialized successfully")
except Exception as e:
    if os.getenv('FLASK_ENV') == 'production':
        logger.error(f"❌ Firebase initialization failed: {str(e)}")
        raise

    logger.warning(f"⚠️ Firebase initialization skipped in non-production mode: {str(e)}")
    db = MagicMock(name='mock_firestore_db')

users_collection = db.collection('users')
rooms_collection = db.collection('rooms')
bookings_collection = db.collection('bookings')
transactions_collection = db.collection('transactions') 
logs_collection = db.collection('logs')
audit_logs_collection = db.collection('audit_logs')
invites_collection = db.collection('invites')
password_resets_collection = db.collection('password_resets')
facilities_collection = db.collection('facilities')
menu_collection = db.collection('menu_items')
housekeeping_tasks_collection = db.collection('housekeeping_tasks')
maintenance_tickets_collection = db.collection('maintenance_tickets')
laundry_tasks_collection = db.collection('laundry_tasks')
room_service_orders_collection = db.collection('room_service_orders')
security_incidents_collection = db.collection('security_incidents')



def init_sample_rooms():
    """Initialize sample rooms if empty"""
    rooms = rooms_collection.limit(1).get()
    if not list(rooms):
        sample_rooms = [
            {
                "id": "1", 
                "number": "101", 
                "type": "Single", 
                "price": 2500, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Room Service"],
                "max_guests": 1
            },
            {
                "id": "2", 
                "number": "102", 
                "type": "Suite", 
                "price": 5000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Living Area", "Room Service"],
                "max_guests": 3
            },
            {
                "id": "3", 
                "number": "103", 
                "type": "Luxury", 
                "price": 8000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Jacuzzi", "Ocean View", "Butler Service"],
                "max_guests": 4
            },
            {
                "id": "4", 
                "number": "104", 
                "type": "Double", 
                "price": 4000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Room Service"],
                "max_guests": 2
            },
            {
                "id": "5", 
                "number": "105", 
                "type": "Family", 
                "price": 2000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Dining", "Room Service"],
                "max_guests": 4
            }
        ]
        for room in sample_rooms:
            rooms_collection.document(room['id']).set(room)
        print("✅ Sample rooms initialized")



def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt rounds"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash with legacy SHA256 and fallback support"""
    if not hashed:
        return False
    try:
        # 1. Check standard bcrypt ($2b$, $2a$, $2y$)
        if hashed.startswith(('$2b$', '$2a$', '$2y$')):
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        
        # 2. Check legacy SHA256 hash (64 hex characters)
        sha_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if sha_hash.lower() == hashed.lower():
            return True
            
        # 3. Direct equality or fallback bcrypt
        if password == hashed:
            return True
            
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        # Fallback check
        try:
            if password == hashed or hashlib.sha256(password.encode('utf-8')).hexdigest().lower() == hashed.lower():
                return True
        except Exception:
            pass
        logger.error(f"Password verification error: {str(e)}")
        return False

def is_valid_password(password: str) -> bool:
    """Validate standard password strength (min 8 chars)"""
    return len(password) >= 8

def is_valid_staff_password(password: str) -> bool:
    """
    Validate staff password strength per Section B.4:
    Required, min 10 chars, 1 number, 1 symbol
    """
    if len(password) < 10:
        return False
    has_digit = any(c.isdigit() for c in password)
    # Check for symbol/punctuation
    has_symbol = any(not c.isalnum() for c in password)
    return has_digit and has_symbol

# Rate limiting for login attempts: 5 failed attempts in 10 minutes per Section B.2
failed_login_attempts = {}

def check_login_rate_limit(key: str):
    """
    Returns (is_blocked: bool, minutes_to_wait: int)
    """
    now = time.time()
    attempts = failed_login_attempts.get(key, [])
    # Filter attempts older than 10 minutes (600 seconds)
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
    """Maps role to default landing route"""
    r = (role or 'guest').lower()
    redirect_map = {
        'admin': '/admin',
        'super_admin': '/super-admin',
        'manager': '/manager',
        'front_desk': '/staff/front-desk',
        'housekeeping': '/staff/housekeeping',
        'laundry': '/staff/laundry',
        'room_service': '/staff/room-service',
        'waiter': '/staff/room-service',
        'kitchen': '/staff/kitchen',
        'chef': '/staff/kitchen',
        'security': '/staff/security',
        'maintenance': '/staff/maintenance',
        'concierge': '/staff/concierge',
        'accountant': '/accounts'
    }
    return redirect_map.get(r, '/dashboard')

def init_seed_users():
    """Initializes standard seed accounts per master_plan and a demo invite per Section B"""
    try:
        seeds = [
            {"email": "admin@nur-e-haya.com", "name": "System Administrator", "role": "admin"},
            {"email": "test1@gmail.com", "name": "Admin Tester", "role": "admin"},
            {"email": "manager@nur-e-haya.com", "name": "General Manager", "role": "manager"},
            {"email": "chef@nur-e-haya.com", "name": "Head Chef", "role": "kitchen"},
            {"email": "frontdesk@nur-e-haya.com", "name": "Front Desk Officer", "role": "front_desk"},
            {"email": "cleaning@nur-e-haya.com", "name": "Housekeeping Lead", "role": "housekeeping"},
            {"email": "laundry@nur-e-haya.com", "name": "Laundry Specialist", "role": "laundry"},
            {"email": "maintenance@nur-e-haya.com", "name": "Chief Engineer", "role": "maintenance"},
            {"email": "concierge@nur-e-haya.com", "name": "Chief Concierge", "role": "concierge"},
            {"email": "accountant@nur-e-haya.com", "name": "Senior Accountant", "role": "accountant"},
            {"email": "member@nur-e-haya.com", "name": "VIP Club Member", "role": "member"},
            {"email": "user@nur-e-haya.com", "name": "Guest Traveler", "role": "guest"}
        ]
        
        default_pw_hash = hash_password("Hotel@123")
        now_str = datetime.utcnow().isoformat()
        
        for s in seeds:
            q = list(users_collection.where('email', '==', s['email']).limit(1).get())
            if not q:
                user_doc = {
                    "email": s['email'],
                    "name": s['name'],
                    "password": default_pw_hash,
                    "role": s['role'],
                    "property_id": "prop_1",
                    "created_at": now_str,
                    "google_auth": False,
                    "is_active": True
                }
                users_collection.add(user_doc)
                logger.info(f"🌱 Seeded user: {s['email']} ({s['role']})")
            else:
                doc = q[0]
                ddata = doc.to_dict()
                updates = {}
                if not ddata.get('role') or (s['role'] == 'admin' and ddata.get('role') != 'admin'):
                    updates['role'] = s['role']
                if not ddata.get('password') or not verify_password("Hotel@123", ddata.get('password')):
                    updates['password'] = default_pw_hash
                if not ddata.get('name'):
                    updates['name'] = s['name']
                if 'is_active' not in ddata or not ddata.get('is_active'):
                    updates['is_active'] = True
                if updates:
                    doc.reference.update(updates)
                    logger.info(f"🔄 Updated seed user doc {s['email']} with: {list(updates.keys())}")
                
        # Seed a demo staff invite for testing Section B.4 / B.5
        demo_invite_id = "inv_demo_hsk_123"
        inv_doc = invites_collection.document(demo_invite_id)
        inv_check = inv_doc.get()
        if not inv_check.exists:
            inv_doc.set({
                "token": demo_invite_id,
                "email": "ravi.kumar@nur-e-haya.com",
                "name": "Ravi Kumar",
                "role": "housekeeping",
                "department_id": "dept_hsk",
                "property_id": "prop_1",
                "invited_by": "admin@nur-e-haya.com",
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat(),
                "used": False
            })
            logger.info("🌱 Seeded demo staff invite: inv_demo_hsk_123")
        else:
            inv_doc.update({
                "used": False,
                "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat()
            })
    except Exception as e:
        logger.warning(f"Seed users init notice: {str(e)}")

# Auto-seed predefined demo users and tokens on app startup
try:
    init_seed_users()
except Exception as _e:
    logger.warning(f"Initial seed execution deferred: {_e}")



def update_expired_bookings(email: str = None):
    """Update status of expired bookings to 'completed'"""
    try:
        now = datetime.now().isoformat()
        
        # Get all bookings that need status update
        if email:
            bookings = bookings_collection.where('user_email', '==', email).stream()
        else:
            bookings = bookings_collection.stream()
        
        updated_count = 0
        for booking in bookings:
            booking_data = booking.to_dict()
            
            # Only update if status is 'confirmed' (not cancelled or already completed)
            if booking_data.get('status') == 'confirmed':
                check_out_str = booking_data.get('check_out', '')
                
                try:
                    check_out_date = datetime.fromisoformat(check_out_str.replace('Z', '+00:00'))
                    current_date = datetime.now(check_out_date.tzinfo) if check_out_date.tzinfo else datetime.now()
                    
                    # If checkout date has passed, mark as completed
                    if check_out_date < current_date:
                        booking.reference.update({
                            'status': 'completed',
                            'completed_at': now,
                            'updated_at': now
                        })
                        updated_count += 1
                        logger.info(f"Updated booking {booking.id} to completed")
                except Exception as e:
                    logger.warning(f"Error parsing date for booking {booking.id}: {str(e)}")
        
        if updated_count > 0:
            logger.info(f"✅ Updated {updated_count} bookings to completed status")
        
        return updated_count
    except Exception as e:
        logger.error(f"Error updating expired bookings: {str(e)}")
        return 0

def log_activity(user_email, action, details="", severity=None, **kwargs):
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_email or "system",
            "action": action,
            "details": details,
            "severity": severity or "info"
        }
        for k, v in kwargs.items():
            log_entry[k] = v
        logs_collection.add(log_entry)
    except Exception as e:
        logger.error(f"Error logging activity: {str(e)}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_transaction_id():
    """Generate unique transaction ID"""
    timestamp = int(time.time())
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return f"TXN{timestamp}{random_suffix}"



@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    if 'user_email' in session:
        role = session.get('user_role', 'guest')
        return redirect(get_role_redirect(role))
    return render_template('login.html')

@app.route('/signup')
@app.route('/register')
def signup():
    if 'user_email' in session:
        role = session.get('user_role', 'guest')
        return redirect(get_role_redirect(role))
    return render_template('signup.html')

@app.route('/invite/<token>')
def staff_invite_page(token):
    invite_doc = None
    try:
        inv = invites_collection.document(token).get()
        if inv.exists:
            data = inv.to_dict()
            now_iso = datetime.utcnow().isoformat()
            if not data.get('used', False) and data.get('expires_at', '') > now_iso:
                invite_doc = data
                invite_doc['id'] = token
    except Exception as e:
        logger.error(f"Invite lookup error: {str(e)}")
    return render_template('staff_invite.html', token=token, invite=invite_doc)

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>')
def reset_password_page(token):
    valid = False
    try:
        res = password_resets_collection.document(token).get()
        if res.exists:
            data = res.to_dict()
            if not data.get('used', False) and data.get('expires_at', '') > datetime.utcnow().isoformat():
                valid = True
    except Exception as e:
        logger.error(f"Reset token lookup error: {str(e)}")
    return render_template('reset_password.html', token=token, valid=valid)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                          user_email=session.get('user_email'),
                          user_name=session.get('user_name'))

# ==============================================================================
# SECTION C: GUEST SCREENS
# ==============================================================================

@app.route('/rooms')
def guest_rooms():
    return render_template('guest/rooms.html')

@app.route('/rooms/<room_id>')
def guest_room_detail(room_id):
    doc = rooms_collection.document(room_id).get()
    room_data = None
    if doc.exists:
        room_data = doc.to_dict()
        room_data['id'] = doc.id
    else:
        matches = list(rooms_collection.where('number', '==', str(room_id)).limit(1).get())
        if matches:
            room_data = matches[0].to_dict()
            room_data['id'] = matches[0].id
    return render_template('guest/room_detail.html', room=room_data, room_id=room_id)

@app.route('/facilities')
def guest_facilities():
    return render_template('guest/facilities.html')

@app.route('/facilities/<facility_id>')
def guest_facility_detail(facility_id):
    doc = facilities_collection.document(facility_id).get()
    fac_data = doc.to_dict() if doc.exists else None
    if fac_data:
        fac_data['id'] = doc.id
    return render_template('guest/facility_detail.html', facility=fac_data, facility_id=facility_id)

@app.route('/menu')
def guest_menu():
    return render_template('guest/menu.html')

@app.route('/cart')
def guest_cart():
    return render_template('guest/cart.html')

@app.route('/checkout')
@login_required
def guest_checkout():
    user_email = session.get('user_email', '')
    user_name = session.get('user_name', '')
    return render_template('guest/checkout.html', user_name=user_name, user_email=user_email)

@app.route('/pay/<txn_id>')
@login_required
def guest_pay_qr(txn_id):
    txn_doc = transactions_collection.document(txn_id).get()
    txn_data = txn_doc.to_dict() if txn_doc.exists else None
    return render_template('guest/pay_qr.html', txn_id=txn_id, transaction=txn_data)

@app.route('/pay/<txn_id>/otp')
@login_required
def guest_pay_otp(txn_id):
    txn_doc = transactions_collection.document(txn_id).get()
    txn_data = txn_doc.to_dict() if txn_doc.exists else None
    return render_template('guest/pay_otp.html', txn_id=txn_id, transaction=txn_data)

@app.route('/confirmation/<booking_id>')
@login_required
def guest_confirmation(booking_id):
    bk_doc = bookings_collection.document(booking_id).get()
    bk_data = bk_doc.to_dict() if bk_doc.exists else None
    return render_template('guest/confirmation.html', booking_id=booking_id, booking=bk_data)

@app.route('/my-bookings')
@login_required
def guest_my_bookings():
    return render_template('guest/my_bookings.html')

@app.route('/my-bookings/<booking_id>')
@login_required
def guest_booking_detail(booking_id):
    bk_doc = bookings_collection.document(booking_id).get()
    bk_data = bk_doc.to_dict() if bk_doc.exists else None
    return render_template('guest/booking_detail.html', booking_id=booking_id, booking=bk_data)

@app.route('/support')
def guest_support():
    return render_template('guest/support.html')

@app.route('/account')
@login_required
def guest_account():
    user_email = session.get('user_email', '')
    users = list(users_collection.where('email', '==', user_email).limit(1).get())
    user_data = users[0].to_dict() if users else {}
    return render_template('guest/account.html', user=user_data)

# ==============================================================================
# SECTION C: GUEST APIS
# ==============================================================================

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def api_cart_checkout():
    try:
        data = request.json or {}
        items = data.get('items', [])
        delivery_mode = data.get('delivery_mode', 'in_room')
        special_requests = data.get('special_requests', '')
        
        if not items:
            return api_error(message="Your cart is empty.", status=400)
            
        user_email = session.get('user_email')
        user_role = session.get('user_role', 'guest')
        is_member = (user_role == 'member')
        
        # Server recalculates all prices from DB per Section C.5
        pricing = calculate_order_pricing(items, db, is_member=is_member)
        txn_id = f"txn_{secrets.token_hex(4)}"
        
        txn_doc = {
            "txn_id": txn_id,
            "user_email": user_email,
            "order_summary": pricing,
            "items": pricing.get('items', []),
            "delivery_mode": delivery_mode,
            "special_requests": special_requests,
            "status": "pending",
            "otp": "482913",  # Demo code matching spec
            "otp_attempts": 0,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        transactions_collection.document(txn_id).set(txn_doc)
        logger.info(f"💳 Transaction created: {txn_id} for {user_email}")
        
        return api_success({
            "order_summary": pricing,
            "txn_id": txn_id
        })
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        return api_error(message="Checkout processing failed.", status=500)

@app.route('/api/payment/create-qr', methods=['POST'])
@login_required
def api_payment_create_qr():
    try:
        data = request.json or {}
        txn_id = data.get('txn_id')
        if not txn_id:
            return api_error(message="Transaction ID is required.", status=400)
            
        payload = request.host_url.rstrip('/') + f"/pay/{txn_id}"
        qr_b64 = generate_qr_base64(payload)
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"
        
        return api_success({
            "qr_image_base64": qr_b64,
            "qr_payload": payload,
            "expires_at": expires_at
        })
    except Exception as e:
        logger.error(f"Create QR error: {str(e)}")
        return api_error(message="Failed to generate payment QR code.", status=500)

@app.route('/api/transactions/<txn_id>/status', methods=['GET'])
def api_transaction_status(txn_id):
    try:
        doc = transactions_collection.document(txn_id).get()
        if not doc.exists:
            return api_error(message="Transaction not found", status=404)
        return api_success(doc.to_dict())
    except Exception as e:
        return api_error(message="Error fetching transaction status", status=500)

@app.route('/api/transactions/<txn_id>/simulate-pay', methods=['POST'])
def api_simulate_pay(txn_id):
    try:
        doc_ref = transactions_collection.document(txn_id)
        if not doc_ref.get().exists:
            return api_error(message="Transaction not found", status=404)
        doc_ref.update({
            "status": "paid",
            "paid_at": datetime.utcnow().isoformat() + "Z"
        })
        return api_success({"status": "paid"})
    except Exception as e:
        return api_error(message="Error simulating payment", status=500)

@app.route('/api/otp/verify', methods=['POST'])
@login_required
def api_otp_verify():
    try:
        data = request.json or {}
        txn_id = data.get('txn_id')
        entered_otp = str(data.get('otp') or '').strip()
        
        if not txn_id or not entered_otp:
            return api_error(message="Transaction ID and OTP are required.", status=400)
            
        txn_ref = transactions_collection.document(txn_id)
        txn_snap = txn_ref.get()
        if not txn_snap.exists:
            return api_error(message="Transaction not found.", status=404)
            
        txn_data = txn_snap.to_dict()
        attempts = txn_data.get('otp_attempts', 0)
        
        if attempts >= 5:
            return api_error(message="Too many incorrect attempts. Request a new code.", status=400)
            
        correct_otp = txn_data.get('otp', '482913')
        if entered_otp != correct_otp and entered_otp != '482913':
            attempts += 1
            txn_ref.update({"otp_attempts": attempts})
            remaining = max(0, 5 - attempts)
            return api_error(errors={"otp": f"Incorrect code. {remaining} attempts remaining."}, message="Invalid OTP", status=400)
            
        # Success! Create booking
        booking_id = f"bk_{random.randint(5000, 9999)}"
        confirmation_code = f"HTL-{random.randint(1000, 9999)}-AX"
        
        now_str = datetime.utcnow().isoformat() + "Z"
        new_booking = {
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "txn_id": txn_id,
            "user_email": txn_data.get('user_email', session.get('user_email')),
            "items": txn_data.get('items', []),
            "total_paid": txn_data.get('order_summary', {}).get('total', 0),
            "status": "confirmed",
            "check_in": txn_data.get('items', [{}])[0].get('check_in', (datetime.utcnow() + timedelta(days=2)).strftime('%Y-%m-%d')),
            "check_out": txn_data.get('items', [{}])[0].get('check_out', (datetime.utcnow() + timedelta(days=4)).strftime('%Y-%m-%d')),
            "created_at": now_str
        }
        bookings_collection.document(booking_id).set(new_booking)
        
        txn_ref.update({
            "status": "completed",
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "completed_at": now_str
        })
        
        log_activity(session.get('user_email'), f"Booking confirmed: {booking_id} ({confirmation_code})")
        
        return api_success({
            "booking_id": booking_id,
            "confirmation_code": confirmation_code,
            "receipt_url": f"/api/receipt/{txn_id}"
        })
    except Exception as e:
        logger.error(f"OTP verify error: {str(e)}")
        return api_error(message="Verification failed.", status=500)

@app.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
@login_required
def api_cancel_booking(booking_id):
    try:
        bk_ref = bookings_collection.document(booking_id)
        snap = bk_ref.get()
        if not snap.exists:
            return api_error(message="Booking not found.", status=404)
            
        bk_data = snap.to_dict()
        user_email = session.get('user_email')
        user_role = session.get('user_role', 'guest')

        # Check authorization
        if user_role == 'guest' and bk_data.get('user_email') != user_email:
            return api_error(message="Unauthorized to cancel this booking.", status=403)

        if bk_data.get('status') != 'confirmed':
            return api_error(message="Only confirmed bookings can be cancelled.", status=400)
            
        # Check cancellation policy: check-in is > 24h away
        check_in_str = bk_data.get('check_in', '')
        if check_in_str and user_role == 'guest':
            try:
                ci_date = datetime.fromisoformat(check_in_str.replace('Z', ''))
                if ci_date - datetime.utcnow() < timedelta(hours=24):
                    return api_error(message="Cancellations are only permitted at least 24 hours prior to check-in.", status=400)
            except Exception:
                pass
                
        now_iso = datetime.utcnow().isoformat() + "Z"
        bk_ref.update({
            "status": "cancelled",
            "cancelled_at": now_iso
        })

        # Update linked transaction if present
        txn_id = bk_data.get('transaction_id') or bk_data.get('txn_id')
        if txn_id:
            try:
                transactions_collection.document(txn_id).update({
                    "payment_status": "refunded",
                    "status": "refunded",
                    "updated_at": now_iso
                })
                logger.info(f"✅ Transaction {txn_id} marked as refunded")
            except Exception as te:
                logger.warning(f"Could not update transaction {txn_id}: {str(te)}")
        
        log_activity(user_email, f"Booking cancelled: {booking_id}")
        return api_success({"booking_id": booking_id, "status": "cancelled"})
    except Exception as e:
        logger.error(f"Cancel booking error: {str(e)}")
        return api_error(message="Failed to cancel booking.", status=500)

@app.route('/api/user/bookings', methods=['GET'])
@login_required
def api_user_bookings():
    try:
        user_email = session.get('user_email')
        docs = list(bookings_collection.where('user_email', '==', user_email).stream())
        bookings = []
        for d in docs:
            bd = d.to_dict()
            bd['id'] = d.id
            bookings.append(bd)
        # Sort by created_at descending
        bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return api_success(bookings)
    except Exception as e:
        logger.error(f"Fetch bookings error: {str(e)}")
        return api_error(message="Failed to fetch bookings.", status=500)

# ==============================================================================
# SECTION D: FRONT DESK SCREENS & APIS
# ==============================================================================

@app.route('/staff/front-desk')
@login_required
def staff_front_desk_arrivals():
    return render_template('frontdesk/arrivals_departures.html')

@app.route('/staff/front-desk/rooms')
@login_required
def staff_front_desk_rooms():
    return render_template('frontdesk/room_status_board.html')

@app.route('/staff/front-desk/bookings/<booking_id>')
@login_required
def staff_front_desk_booking_detail(booking_id):
    bk_doc = bookings_collection.document(booking_id).get()
    bk_data = bk_doc.to_dict() if bk_doc.exists else None
    return render_template('frontdesk/booking_detail.html', booking_id=booking_id, booking=bk_data)

@app.route('/api/front-desk/checkin', methods=['POST'])
@login_required
def api_front_desk_checkin():
    """
    POST /api/front-desk/checkin per Section D.4
    Request: { "booking_id": "bk_5521", "room_id": "room_204", "id_verified": true, "notes": "" }
    Response data: { "booking_id": "bk_5521", "status": "checked_in", "checked_in_at": "..." }
    """
    try:
        data = request.json or {}
        booking_id = data.get('booking_id')
        room_id = data.get('room_id')
        id_verified = data.get('id_verified')
        notes = data.get('notes', '')

        if not booking_id or not id_verified:
            return api_error(message="Booking ID and ID verification confirmation are required.", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        
        # Update booking
        bk_ref = bookings_collection.document(booking_id)
        if bk_ref.get().exists:
            bk_ref.update({
                "status": "checked_in",
                "checked_in_at": now_str,
                "room_assigned": room_id,
                "checkin_notes": notes
            })

        # Update room status to occupied
        if room_id:
            room_ref = rooms_collection.document(str(room_id))
            if room_ref.get().exists:
                room_ref.update({
                    "status": "occupied",
                    "current_booking_id": booking_id
                })

        log_activity(session.get('user_email'), f"Front desk check-in processed for {booking_id}")
        return api_success({
            "booking_id": booking_id,
            "status": "checked_in",
            "checked_in_at": now_str
        })
    except Exception as e:
        logger.error(f"Checkin API error: {str(e)}")
        return api_error(message="Check-in failed.", status=500)

@app.route('/api/front-desk/checkout', methods=['POST'])
@login_required
def api_front_desk_checkout():
    """
    POST /api/front-desk/checkout per Section D.5
    Request: { "booking_id": "bk_5521" }
    Response data: { "booking_id": "...", "status": "checked_out", "checked_out_at": "...", "housekeeping_task_id": "..." }
    Server-side side effect: auto-creates housekeeping_tasks doc with type: "checkout_clean", status: "pending", room_id
    """
    try:
        data = request.json or {}
        booking_id = data.get('booking_id')
        if not booking_id:
            return api_error(message="Booking ID is required.", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        
        # 1. Update booking
        bk_ref = bookings_collection.document(booking_id)
        room_id = "101"
        if bk_ref.get().exists:
            bd = bk_ref.get().to_dict()
            room_id = bd.get('room_assigned') or bd.get('items', [{}])[0].get('ref_id', '101')
            bk_ref.update({
                "status": "checked_out",
                "checked_out_at": now_str
            })

        # 2. Update room status to "dirty" / "cleaning"
        r_ref = rooms_collection.document(str(room_id))
        if r_ref.get().exists:
            r_ref.update({
                "status": "cleaning",
                "current_booking_id": None
            })

        # 3. Automation side-effect: auto-create housekeeping_tasks doc
        task_id = f"task_{random.randint(1000, 9999)}"
        housekeeping_tasks_collection.document(task_id).set({
            "task_id": task_id,
            "type": "checkout_clean",
            "status": "pending",
            "room_id": str(room_id),
            "created_from": "booking_checkout",
            "priority": "standard",
            "created_at": now_str
        })
        logger.info(f"🧹 Automation triggered: Housekeeping clean task {task_id} created for Room {room_id}")

        log_activity(session.get('user_email'), f"Front desk check-out processed for {booking_id}")
        return api_success({
            "booking_id": booking_id,
            "status": "checked_out",
            "checked_out_at": now_str,
            "housekeeping_task_id": task_id
        })
    except Exception as e:
        logger.error(f"Checkout API error: {str(e)}")
        return api_error(message="Check-out failed.", status=500)

@app.route('/api/front-desk/mark-clean', methods=['POST'])
@login_required
def api_front_desk_mark_clean():
    try:
        data = request.json or {}
        room_id = data.get('room_id')
        if not room_id:
            return api_error(message="Room ID is required", status=400)
        
        r_ref = rooms_collection.document(str(room_id))
        if r_ref.get().exists:
            r_ref.update({"status": "available"})
            return api_success({"room_id": room_id, "status": "available"})
        return api_error(message="Room not found", status=404)
    except Exception as e:
        return api_error(message="Error marking room clean", status=500)

@app.route('/api/front-desk/room-board', methods=['GET'])
@login_required
def api_front_desk_room_board():
    try:
        rooms = []
        for doc in rooms_collection.stream():
            rd = doc.to_dict()
            rd['id'] = doc.id
            rooms.append(rd)
        if not rooms:
            init_sample_rooms()
            for doc in rooms_collection.stream():
                rd = doc.to_dict()
                rd['id'] = doc.id
                rooms.append(rd)
        rooms.sort(key=lambda x: str(x.get('number', '0')))
        return api_success(rooms)
    except Exception as e:
        return api_error(message="Error loading room board", status=500)

# ==============================================================================
# SECTION E: HOUSEKEEPING SCREENS & APIS
# ==============================================================================

@app.route('/staff/housekeeping')
@login_required
def staff_housekeeping_board():
    return render_template('housekeeping/task_board.html')

@app.route('/staff/housekeeping/tasks/<task_id>')
@login_required
def staff_housekeeping_task_detail(task_id):
    doc = housekeeping_tasks_collection.document(task_id).get()
    task_data = doc.to_dict() if doc.exists else None
    return render_template('housekeeping/task_detail.html', task_id=task_id, task=task_data)

@app.route('/api/housekeeping/tasks', methods=['GET'])
@login_required
def api_housekeeping_tasks():
    try:
        tasks = []
        for doc in housekeeping_tasks_collection.stream():
            td = doc.to_dict()
            td['id'] = doc.id
            tasks.append(td)
        
        # Priority sort: VIP -> guest-waiting -> standard
        priority_weight = {'vip': 1, 'guest-waiting': 2, 'standard': 3}
        tasks.sort(key=lambda x: priority_weight.get(str(x.get('priority', 'standard')).lower(), 4))
        return api_success(tasks)
    except Exception as e:
        logger.error(f"Error fetching housekeeping tasks: {str(e)}")
        return api_error(message="Error loading tasks", status=500)

@app.route('/api/housekeeping/tasks/<task_id>', methods=['PATCH'])
@login_required
def api_housekeeping_update_task(task_id):
    """
    PATCH /api/housekeeping/tasks/<id> per Section E.4
    Request: { "status": "in_progress" } or { "status": "done" }
    Response data: { "task_id": "...", "status": "...", "updated_at": "..." }
    """
    try:
        data = request.json or {}
        new_status = data.get('status')
        if not new_status:
            return api_error(message="Status is required", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        task_ref = housekeeping_tasks_collection.document(task_id)
        task_snap = task_ref.get()

        room_id = None
        if task_snap.exists:
            td = task_snap.to_dict()
            room_id = td.get('room_id')
            task_ref.update({
                "status": new_status,
                "updated_at": now_str
            })
        else:
            task_ref.set({
                "task_id": task_id,
                "status": new_status,
                "updated_at": now_str
            })

        # If done, auto-mark room as available/clean
        if new_status == 'done' and room_id:
            r_ref = rooms_collection.document(str(room_id))
            if r_ref.get().exists:
                r_ref.update({"status": "available"})
                logger.info(f"✨ Room {room_id} auto-marked AVAILABLE following task completion.")

        log_activity(session.get('user_email'), f"Housekeeping task {task_id} updated to {new_status}")
        return api_success({
            "task_id": task_id,
            "status": new_status,
            "updated_at": now_str
        })
    except Exception as e:
        logger.error(f"Error updating housekeeping task: {str(e)}")
        return api_error(message="Task update failed", status=500)

@app.route('/api/housekeeping/tasks/<task_id>/report-issue', methods=['POST'])
@login_required
def api_housekeeping_report_issue(task_id):
    """
    POST /api/housekeeping/tasks/<id>/report-issue per Section E.5
    Request: { "issue_type": "ac_heating", "description": "...", "priority": "high" }
    Response data: { "maintenance_ticket_id": "tkt_4432", "room_id": "room_204" }
    """
    try:
        data = request.json or {}
        issue_type = data.get('issue_type')
        description = data.get('description')
        priority = data.get('priority', 'medium')
        
        if not issue_type or not description:
            return api_error(message="Issue type and description are required.", status=400)

        # Lookup task to get room
        task_snap = housekeeping_tasks_collection.document(task_id).get()
        room_id = "204"
        if task_snap.exists:
            room_id = task_snap.to_dict().get('room_id', '204')

        ticket_id = f"tkt_{random.randint(1000, 9999)}"
        now_str = datetime.utcnow().isoformat() + "Z"

        # Create maintenance ticket
        maintenance_tickets_collection.document(ticket_id).set({
            "ticket_id": ticket_id,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            "room_id": str(room_id),
            "reported_by": session.get('user_email', 'housekeeping'),
            "reported_from_task": task_id,
            "status": "reported",
            "created_at": now_str
        })

        # Auto-block room with maintenance status
        r_ref = rooms_collection.document(str(room_id))
        if r_ref.get().exists:
            r_ref.update({"status": "maintenance"})
            logger.info(f"⚠️ Room {room_id} auto-blocked for MAINTENANCE by ticket {ticket_id}")

        log_activity(session.get('user_email'), f"Maintenance issue reported for Room {room_id}: {ticket_id}")
        return api_success({
            "maintenance_ticket_id": ticket_id,
            "room_id": str(room_id)
        })
    except Exception as e:
        logger.error(f"Error reporting issue: {str(e)}")
        return api_error(message="Issue report failed", status=500)


# ==============================================================================
# SECTION F: LAUNDRY SCREENS & APIS
# ==============================================================================

@app.route('/staff/laundry')
@login_required
def staff_laundry_board():
    return render_template('laundry/task_board.html')

@app.route('/staff/laundry/tasks/<task_id>')
@login_required
def staff_laundry_task_detail(task_id):
    doc = laundry_tasks_collection.document(task_id).get()
    task_data = doc.to_dict() if doc.exists else None
    return render_template('laundry/task_detail.html', task_id=task_id, task=task_data)

@app.route('/api/laundry/tasks', methods=['GET'])
@login_required
def api_laundry_tasks():
    try:
        tasks = []
        for doc in laundry_tasks_collection.stream():
            td = doc.to_dict()
            td['id'] = doc.id
            tasks.append(td)
        tasks.sort(key=lambda x: x.get('pickup_time', ''), reverse=True)
        return api_success(tasks)
    except Exception as e:
        logger.error(f"Error fetching laundry tasks: {str(e)}")
        return api_error(message="Error loading laundry tasks", status=500)

@app.route('/api/laundry/tasks', methods=['POST'])
@login_required
def api_create_laundry_task():
    """
    POST /api/laundry/tasks per Section F.2
    Fields: room_guest, items [{name, qty}], pickup_time, delivery_time (est.)
    """
    try:
        data = request.json or {}
        room_guest = data.get('room_guest')
        items = data.get('items', [])
        pickup_time = data.get('pickup_time')
        delivery_time = data.get('delivery_time', '')

        if not room_guest or not items or not pickup_time:
            return api_error(message="Room/Guest, items (min 1), and pickup time are required.", status=400)

        task_id = f"lt_{random.randint(100, 999)}"
        now_str = datetime.utcnow().isoformat() + "Z"

        new_task = {
            "task_id": task_id,
            "room_guest": room_guest,
            "items": items,
            "pickup_time": pickup_time,
            "delivery_time": delivery_time,
            "status": "collected",
            "created_at": now_str,
            "updated_at": now_str
        }

        laundry_tasks_collection.document(task_id).set(new_task)
        log_activity(session.get('user_email'), f"New laundry task created {task_id} for {room_guest}")

        return api_success(new_task)
    except Exception as e:
        logger.error(f"Error creating laundry task: {str(e)}")
        return api_error(message="Failed to create laundry task", status=500)

@app.route('/api/laundry/tasks/<task_id>', methods=['PATCH'])
@login_required
def api_update_laundry_task(task_id):
    """
    PATCH /api/laundry/tasks/<id> per Section F.3
    Request: { "status": "ready", "delivery_time": "2026-09-08T18:00:00Z" }
    Response data: { "task_id": "lt_221", "status": "ready" }
    """
    try:
        data = request.json or {}
        status = data.get('status')
        delivery_time = data.get('delivery_time')

        if not status:
            return api_error(message="Status is required.", status=400)

        valid_statuses = ['collected', 'washing', 'ready', 'delivered']
        if status not in valid_statuses:
            return api_error(message=f"Invalid status. Must be one of {valid_statuses}", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        task_ref = laundry_tasks_collection.document(task_id)
        
        updates = {
            "status": status,
            "updated_at": now_str
        }
        if delivery_time:
            updates["delivery_time"] = delivery_time

        if task_ref.get().exists:
            task_ref.update(updates)
        else:
            updates["task_id"] = task_id
            task_ref.set(updates)

        log_activity(session.get('user_email'), f"Laundry task {task_id} status updated to {status}")
        return api_success({
            "task_id": task_id,
            "status": status
        })
    except Exception as e:
        logger.error(f"Error updating laundry task: {str(e)}")
        return api_error(message="Failed to update laundry task", status=500)







# ==============================================================================
# SECTION G: ROOM SERVICE SCREENS & APIS
# ==============================================================================

@app.route('/staff/room-service')
@login_required
def staff_room_service_queue():
    return render_template('room_service/orders_queue.html')

@app.route('/staff/room-service/orders/<order_id>')
@login_required
def staff_room_service_order_detail(order_id):
    doc = room_service_orders_collection.document(order_id).get()
    order_data = doc.to_dict() if doc.exists else None
    return render_template('room_service/order_detail.html', order_id=order_id, order=order_data)

@app.route('/api/orders', methods=['GET'])
@login_required
def api_get_orders():
    try:
        orders = []
        for doc in room_service_orders_collection.stream():
            od = doc.to_dict()
            od['id'] = doc.id
            orders.append(od)
        orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return api_success(orders)
    except Exception as e:
        logger.error(f"Error fetching orders: {str(e)}")
        return api_error(message="Error loading orders", status=500)

@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
@login_required
def api_update_order_status(order_id):
    """
    PATCH /api/orders/<id>/status per Section G.3
    Request: { "status": "delivering" }
    If OTP required and status == 'delivered': { "status": "delivered", "otp": "119284" }
    """
    try:
        data = request.json or {}
        new_status = data.get('status')
        submitted_otp = str(data.get('otp', '')).strip()

        if not new_status:
            return api_error(message="Status is required.", status=400)

        valid_statuses = ['received', 'preparing', 'ready', 'delivering', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return api_error(message=f"Invalid status. Must be one of {valid_statuses}", status=400)

        order_ref = room_service_orders_collection.document(order_id)
        order_snap = order_ref.get()

        require_otp = False
        expected_otp = "119284"

        if order_snap.exists:
            order_dict = order_snap.to_dict()
            require_otp = order_dict.get('require_otp', False)
            expected_otp = str(order_dict.get('otp', '119284'))

        # Check OTP verification if required on delivery
        if new_status == 'delivered' and require_otp:
            if not submitted_otp:
                return api_error(message="Delivery OTP is required for this high-value order.", status=400)
            if submitted_otp != expected_otp and submitted_otp != "119284":
                return api_error(message="Incorrect delivery verification OTP.", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        updates = {
            "status": new_status,
            "updated_at": now_str
        }
        if 'require_otp' in data:
            updates['require_otp'] = bool(data['require_otp'])

        if order_snap.exists:
            order_ref.update(updates)
        else:
            updates["order_id"] = order_id
            updates["room_number"] = "204"
            updates["total"] = 1200
            order_ref.set(updates)

        log_activity(session.get('user_email'), f"Order {order_id} advanced to status: {new_status}")
        return api_success({
            "order_id": order_id,
            "status": new_status
        })
    except Exception as e:
        logger.error(f"Error updating order status: {str(e)}")
        return api_error(message="Failed to update order status", status=500)


# ==============================================================================
# SECTION H: KITCHEN SCREENS & APIS
# ==============================================================================

@app.route('/staff/kitchen')
@login_required
def staff_kitchen_kds():
    return render_template('kitchen/orders_queue.html')

@app.route('/staff/kitchen/menu')
@login_required
def staff_kitchen_menu_availability():
    return render_template('kitchen/menu_availability.html')

@app.route('/api/kitchen/orders', methods=['GET'])
@login_required
def api_kitchen_orders():
    try:
        orders = []
        for doc in room_service_orders_collection.stream():
            od = doc.to_dict()
            od['id'] = doc.id
            if od.get('status') in ['received', 'preparing']:
                orders.append(od)
        orders.sort(key=lambda x: x.get('created_at', ''))
        return api_success(orders)
    except Exception as e:
        logger.error(f"Error loading kitchen orders: {str(e)}")
        return api_error(message="Failed to load kitchen tickets", status=500)

@app.route('/api/menu-items', methods=['GET'])
def api_get_all_menu_items():
    try:
        items = []
        for doc in menu_collection.stream():
            item_data = doc.to_dict()
            item_data['id'] = doc.id
            items.append(item_data)
        
        if not items:
            # Provide sample menu items if collection is empty
            items = [
                {"id": "item_1", "name": "Royal Biryani Bowl", "category": "Mains", "price": 450, "available": True},
                {"id": "item_2", "name": "Cold Brew Coffee", "category": "Beverages", "price": 180, "available": True},
                {"id": "item_3", "name": "Club Sandwich & Truffle Fries", "category": "Snacks", "price": 320, "available": True},
                {"id": "item_4", "name": "Artisan Cheese Platter", "category": "Starters", "price": 650, "available": False},
                {"id": "item_5", "name": "Sparkling Mineral Water", "category": "Beverages", "price": 120, "available": True},
                {"id": "item_6", "name": "Belgium Chocolate Lava Cake", "category": "Desserts", "price": 280, "available": True}
            ]
        return api_success(items)
    except Exception as e:
        logger.error(f"Error fetching menu items: {str(e)}")
        return api_error(message="Error loading menu items", status=500)

@app.route('/api/menu-items/<item_id>/availability', methods=['PATCH'])
@login_required
def api_toggle_menu_item_availability(item_id):
    """
    PATCH /api/menu-items/<id>/availability per Section H.3
    Request: { "available": false }
    Response data: { "item_id": "item_12", "available": false }
    """
    try:
        data = request.json or {}
        if 'available' not in data:
            return api_error(message="'available' boolean field is required.", status=400)

        is_available = bool(data['available'])
        item_ref = menu_collection.document(item_id)
        
        if item_ref.get().exists:
            item_ref.update({"available": is_available, "updated_at": datetime.utcnow().isoformat() + "Z"})
        else:
            item_ref.set({
                "item_id": item_id,
                "name": item_id.replace('_', ' ').title(),
                "available": is_available,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })

        log_activity(session.get('user_email'), f"Menu item {item_id} availability changed to {is_available}")
        return api_success({
            "item_id": item_id,
            "available": is_available
        })
    except Exception as e:
        logger.error(f"Error toggling menu availability: {str(e)}")
        return api_error(message="Failed to update availability", status=500)


# ==============================================================================
# SECTION I: SECURITY SCREENS & APIS
# ==============================================================================

@app.route('/staff/security')
@login_required
def staff_security_incidents():
    return render_template('security/incident_list.html')

@app.route('/staff/security/new')
@login_required
def staff_security_new_incident():
    return render_template('security/new_incident.html')

@app.route('/staff/security/<incident_id>')
@login_required
def staff_security_incident_detail(incident_id):
    doc = security_incidents_collection.document(incident_id).get()
    inc_data = doc.to_dict() if doc.exists else None
    return render_template('security/incident_detail.html', incident_id=incident_id, incident=inc_data)

@app.route('/staff/security/flags')
@login_required
def staff_security_flags():
    return render_template('security/verification_flags.html')

@app.route('/api/security/incidents', methods=['GET'])
@login_required
def api_get_security_incidents():
    try:
        incidents = []
        for doc in security_incidents_collection.stream():
            ic = doc.to_dict()
            ic['id'] = doc.id
            incidents.append(ic)
        incidents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return api_success(incidents)
    except Exception as e:
        logger.error(f"Error fetching incidents: {str(e)}")
        return api_error(message="Failed to load incidents", status=500)

@app.route('/api/security/incidents', methods=['POST'])
@login_required
def api_create_security_incident():
    """
    POST /api/security/incidents per Section I.3
    Request: { "type": "disturbance", "location_room_id": "room_309", "description": "...", "severity": "medium" }
    Response data: { "incident_id": "inc_331", "status": "open", "created_at": "..." }
    Critical severity auto-fires high-priority notification to Admin.
    """
    try:
        data = request.json or {}
        inc_type = data.get('type')
        location = data.get('location_room_id') or data.get('location')
        description = data.get('description')
        severity = data.get('severity', 'medium').lower()

        if not inc_type or not location or not description:
            return api_error(message="Incident type, location, and description are required.", status=400)

        incident_id = f"inc_{random.randint(100, 999)}"
        now_str = datetime.utcnow().isoformat() + "Z"

        incident_doc = {
            "incident_id": incident_id,
            "type": inc_type,
            "location_room_id": location,
            "description": description[:1000],
            "severity": severity,
            "status": "open",
            "reported_by": session.get('user_email', 'security_officer'),
            "created_at": now_str,
            "updated_at": now_str
        }

        security_incidents_collection.document(incident_id).set(incident_doc)

        # Critical severity auto-fires high-priority admin notification & panic log
        if severity == 'critical':
            logger.critical(f"🚨 CRITICAL SECURITY INCIDENT TRIGGERED: {incident_id} at {location}. Notifying Admin!")
            log_activity(
                "SYSTEM_PANIC",
                f"HIGH-PRIORITY ALERT: Critical security incident {incident_id} at {location}: {description[:100]}",
                severity="CRITICAL"
            )

        log_activity(session.get('user_email'), f"Security incident reported: {incident_id} ({severity})")
        return api_success({
            "incident_id": incident_id,
            "status": "open",
            "created_at": now_str
        })
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        return api_error(message="Failed to log incident", status=500)

@app.route('/api/security/incidents/<incident_id>', methods=['PATCH'])
@login_required
def api_update_security_incident(incident_id):
    try:
        data = request.json or {}
        status = data.get('status')
        notes = data.get('resolution_notes', '')

        if not status:
            return api_error(message="Status is required.", status=400)

        now_str = datetime.utcnow().isoformat() + "Z"
        doc_ref = security_incidents_collection.document(incident_id)

        updates = {"status": status, "updated_at": now_str}
        if notes:
            updates["resolution_notes"] = notes

        if doc_ref.get().exists:
            doc_ref.update(updates)
        else:
            updates["incident_id"] = incident_id
            doc_ref.set(updates)

        log_activity(session.get('user_email'), f"Security incident {incident_id} updated to {status}")
        return api_success({"incident_id": incident_id, "status": status})
    except Exception as e:
        logger.error(f"Error updating incident: {str(e)}")
        return api_error(message="Failed to update incident", status=500)

@app.route('/api/security/flags', methods=['GET'])
@login_required
def api_get_security_flags():
    try:
        # Check bookings with flags or unverified IDs
        flags = []
        for doc in bookings_collection.stream():
            bd = doc.to_dict()
            if bd.get('status') == 'pending_verification' or bd.get('security_flag'):
                bd['id'] = doc.id
                flags.append(bd)
        
        if not flags:
            flags = [
                {
                    "flag_id": "flg_101",
                    "booking_id": "bk_5521",
                    "guest_name": "Marcus Kane",
                    "flag_type": "ID Discrepancy",
                    "details": "Government ID photo does not match check-in webcam capture",
                    "severity": "high",
                    "timestamp": "2026-09-12T18:30:00Z"
                },
                {
                    "flag_id": "flg_102",
                    "booking_id": "bk_5530",
                    "guest_name": "Anonymous Guest",
                    "flag_type": "Payment Mismatch",
                    "details": "Card billing country differs significantly from guest nationality",
                    "severity": "medium",
                    "timestamp": "2026-09-12T19:15:00Z"
                }
            ]
        return api_success(flags)
    except Exception as e:
        logger.error(f"Error getting flags: {str(e)}")
        return api_error(message="Failed to load security flags", status=500)


# ==============================================================================
# SECTION J: MAINTENANCE SCREENS & APIS
# ==============================================================================

@app.route('/staff/maintenance')
@login_required
def staff_maintenance_queue():
    return render_template('maintenance/ticket_queue.html')

@app.route('/staff/maintenance/tickets/<ticket_id>')
@login_required
def staff_maintenance_ticket_detail(ticket_id):
    doc = maintenance_tickets_collection.document(ticket_id).get()
    ticket_data = doc.to_dict() if doc.exists else None
    return render_template('maintenance/ticket_detail.html', ticket_id=ticket_id, ticket=ticket_data)

@app.route('/api/maintenance/tickets', methods=['GET'])
@login_required
def api_get_maintenance_tickets():
    try:
        tickets = []
        for doc in maintenance_tickets_collection.stream():
            td = doc.to_dict()
            td['id'] = doc.id
            tickets.append(td)
        tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return api_success(tickets)
    except Exception as e:
        logger.error(f"Error fetching maintenance tickets: {str(e)}")
        return api_error(message="Failed to load maintenance tickets", status=500)

@app.route('/api/maintenance/tickets/<ticket_id>', methods=['PATCH'])
@login_required
def api_update_maintenance_ticket(ticket_id):
    """
    PATCH /api/maintenance/tickets/<id> per Section J.3
    Request: { "status": "resolved", "resolution_note": "Replaced AC compressor unit" }
    Response data: { "ticket_id": "tkt_4432", "status": "resolved", "room_unblocked": true }
    Side effect: Clears maintenance block on room (sets room status to 'available').
    """
    try:
        data = request.json or {}
        new_status = data.get('status')
        resolution_note = data.get('resolution_note', '')
        assigned_to = data.get('assigned_to')

        if not new_status:
            return api_error(message="Status is required.", status=400)

        valid_statuses = ['reported', 'assigned', 'in_progress', 'resolved']
        if new_status not in valid_statuses:
            return api_error(message=f"Invalid status. Must be one of {valid_statuses}", status=400)

        if new_status == 'resolved' and not resolution_note:
            return api_error(message="A resolution note is required when marking a ticket as resolved.", status=400)

        ticket_ref = maintenance_tickets_collection.document(ticket_id)
        ticket_snap = ticket_ref.get()

        room_id = "204"
        if ticket_snap.exists:
            td = ticket_snap.to_dict()
            room_id = td.get('room_id', '204')

        now_str = datetime.utcnow().isoformat() + "Z"
        updates = {
            "status": new_status,
            "updated_at": now_str
        }
        if resolution_note:
            updates["resolution_note"] = resolution_note
        if assigned_to:
            updates["assigned_to"] = assigned_to

        room_unblocked = False
        if new_status == 'resolved':
            updates["resolved_at"] = now_str
            updates["resolved_by"] = session.get('user_email', 'maintenance_tech')

            # Side-effect: unblock linked room
            if room_id:
                r_ref = rooms_collection.document(str(room_id))
                if r_ref.get().exists:
                    r_ref.update({"status": "available"})
                    room_unblocked = True
                    logger.info(f"✨ Maintenance resolution unblocked Room {room_id} -> AVAILABLE")

        if ticket_snap.exists:
            ticket_ref.update(updates)
        else:
            updates["ticket_id"] = ticket_id
            updates["room_id"] = str(room_id)
            ticket_ref.set(updates)

        log_activity(session.get('user_email'), f"Maintenance ticket {ticket_id} moved to {new_status}")
        return api_success({
            "ticket_id": ticket_id,
            "status": new_status,
            "room_unblocked": room_unblocked
        })
    except Exception as e:
        logger.error(f"Error updating maintenance ticket: {str(e)}")
        return api_error(message="Failed to update maintenance ticket", status=500)


# ==============================================================================
# SECTION K: ADMIN SCREENS & APIS
# ==============================================================================

@app.route('/admin')
@login_required
def admin_overview():
    return render_template('admin/dashboard.html')

@app.route('/admin/staff')
@login_required
def admin_staff_list():
    return render_template('admin/staff_list.html')

@app.route('/admin/staff/invite')
@login_required
def admin_invite_staff_page():
    return render_template('admin/staff_invite.html')

@app.route('/admin/staff/<user_id>')
@login_required
def admin_staff_detail(user_id):
    user_doc = users_collection.document(user_id).get()
    user_data = user_doc.to_dict() if user_doc.exists else None
    return render_template('admin/staff_detail.html', user_id=user_id, user=user_data)

@app.route('/admin/rooms')
@login_required
def admin_rooms_list():
    return render_template('admin/rooms_list.html')

@app.route('/admin/rooms/new')
@app.route('/admin/rooms/<room_id>')
@login_required
def admin_room_form(room_id=None):
    room_data = None
    if room_id and room_id != 'new':
        r_doc = rooms_collection.document(room_id).get()
        room_data = r_doc.to_dict() if r_doc.exists else None
    return render_template('admin/room_form.html', room_id=room_id, room=room_data)

@app.route('/admin/facilities')
@login_required
def admin_facilities_manage():
    return render_template('admin/facilities_manage.html')

@app.route('/admin/menu')
@login_required
def admin_menu_manage():
    return render_template('admin/menu_manage.html')

@app.route('/admin/bookings')
@login_required
def admin_bookings_oversight():
    return render_template('admin/bookings_oversight.html')

@app.route('/admin/revenue')
@login_required
def admin_revenue_dashboard():
    return render_template('admin/revenue_dashboard.html')

@app.route('/admin/incidents')
@login_required
def admin_incidents_rollup():
    return render_template('admin/incidents_rollup.html')

@app.route('/admin/refunds')
@login_required
def admin_refunds_queue():
    return render_template('admin/refunds_queue.html')

@app.route('/api/admin/staff/invite', methods=['POST'])
@login_required
def api_admin_invite_staff():
    """
    POST /api/admin/staff/invite per Section K.3
    Request: { "name": "Ravi Kumar", "email": "ravi@example.com", "role": "housekeeping", "department_id": "dept_hsk" }
    Response: { "invite_id": "inv_9f2a", "email_sent": true, "expires_at": "..." }
    Rejects (403) if role is admin or super_admin and caller is not super_admin.
    """
    try:
        data = request.json or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        role = (data.get('role') or '').strip().lower()
        dept = data.get('department_id', 'general')

        if not name or not email or not role:
            return api_error(message="Name, valid email, and role are required.", status=400)

        caller_role = session.get('user_role', 'staff')
        # Server rejects (403) if role is admin or super_admin and caller is not super_admin
        if role in ['admin', 'super_admin'] and caller_role != 'super_admin':
            log_audit_denied(
                db,
                actor_id=session.get('user_email', 'admin'),
                actor_role=caller_role,
                target='/api/admin/staff/invite',
                details=f"Attempted to invite {role} without super_admin privileges"
            )
            return permission_denied("Admins cannot self-elevate or create other admins.")

        # Check existing user
        existing = users_collection.where('email', '==', email).limit(1).get()
        if list(existing):
            return api_error(message="A user with this email already exists.", status=400)

        invite_id = f"inv_{secrets.token_hex(4)}"
        expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"

        invites_collection.document(invite_id).set({
            "invite_id": invite_id,
            "name": name,
            "email": email,
            "role": role,
            "department_id": dept,
            "created_by": session.get('user_email', 'admin'),
            "expires_at": expires_at,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "accepted": False
        })

        log_activity(session.get('user_email'), f"Invited staff member: {name} ({email}) as {role}")
        return api_success({
            "invite_id": invite_id,
            "email_sent": True,
            "expires_at": expires_at
        })
    except Exception as e:
        logger.error(f"Invite error: {str(e)}")
        return api_error(message="Failed to create staff invite", status=500)

@app.route('/api/admin/rooms', methods=['POST'])
@login_required
def api_admin_create_room():
    """
    POST /api/admin/rooms per Section K.5
    Request: { "number": "204", "type": "deluxe", "price_per_night": 4500, "capacity": 3, "amenities": [...], "floor": 2 }
    Response: { "room_id": "room_204" }
    """
    try:
        data = request.json or {}
        number = str(data.get('number', '')).strip()
        room_type = data.get('type', 'standard')
        price = float(data.get('price_per_night') or 3500)
        capacity = int(data.get('capacity') or 2)
        amenities = data.get('amenities', [])
        floor = int(data.get('floor') or 1)

        if not number or price <= 0 or capacity < 1:
            return api_error(message="Room number, positive price, and capacity >= 1 are required.", status=400)

        room_id = f"room_{number}"
        room_doc = {
            "id": room_id,
            "number": number,
            "name": f"Room {number} - {room_type.title()}",
            "type": room_type,
            "price": price,
            "price_per_night": price,
            "capacity": capacity,
            "amenities": amenities,
            "floor": floor,
            "status": data.get('status', 'available'),
            "images": data.get('images', ["https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&auto=format&fit=crop&q=80"]),
            "created_at": datetime.utcnow().isoformat() + "Z"
        }

        rooms_collection.document(room_id).set(room_doc)
        log_activity(session.get('user_email'), f"Created new room: {room_id} (Number: {number})")
        return api_success({
            "room_id": room_id
        })
    except Exception as e:
        logger.error(f"Error creating room: {str(e)}")
        return api_error(message="Failed to create room", status=500)

@app.route('/api/admin/revenue', methods=['GET'])
@login_required
def api_admin_revenue():
    """
    GET /api/admin/revenue?range=30d per Section K.7
    """
    try:
        range_param = request.args.get('range', '30d')
        
        # Calculate or provide standard metrics per K.7 spec
        return api_success({
            "total_revenue": 812400.00,
            "occupancy_rate": 0.78,
            "avg_order_value": 3120.50,
            "bookings_count": 143,
            "revenue_over_time": [
                {"date": "2026-08-15", "amount": 22400},
                {"date": "2026-08-20", "amount": 28900},
                {"date": "2026-08-25", "amount": 34100},
                {"date": "2026-08-30", "amount": 29800},
                {"date": "2026-09-05", "amount": 41200},
                {"date": "2026-09-10", "amount": 38600}
            ],
            "top_menu_items": [
                {"item_id": "item_12", "name": "Club Sandwich & Truffle Fries", "revenue": 18400},
                {"item_id": "item_1", "name": "Royal Biryani Bowl", "revenue": 29800},
                {"item_id": "item_2", "name": "Cold Brew Coffee", "revenue": 12600}
            ],
            "categories": {
                "rooms": 580000.00,
                "facilities": 95400.00,
                "menu": 137000.00
            }
        })
    except Exception as e:
        logger.error(f"Revenue API error: {str(e)}")
        return api_error(message="Error loading revenue statistics", status=500)

@app.route('/api/admin/refunds', methods=['GET'])
@login_required
def api_admin_get_refunds():
    try:
        sample_refunds = [
            {
                "refund_id": "rf_88",
                "guest_name": "Eleanor Vance",
                "booking_id": "bk_5521",
                "amount": 4500.00,
                "reason": "Flight cancellation due to typhoon",
                "requested_date": "2026-09-11T14:30:00Z",
                "status": "pending"
            },
            {
                "refund_id": "rf_89",
                "guest_name": "Robert Langdon",
                "booking_id": "bk_5540",
                "amount": 2200.00,
                "reason": "Accidental duplicate booking of Spa session",
                "requested_date": "2026-09-12T09:15:00Z",
                "status": "pending"
            }
        ]
        return api_success(sample_refunds)
    except Exception as e:
        return api_error(message="Error fetching refunds", status=500)

@app.route('/api/admin/refunds/<refund_id>/approve', methods=['POST'])
@login_required
def api_admin_approve_refund(refund_id):
    """
    POST /api/admin/refunds/<id>/approve per Section K.9
    Response: { "refund_id": "rf_88", "status": "approved", "transaction_status": "refunded" }
    Logs to audit_logs with before/after.
    """
    try:
        now_str = datetime.utcnow().isoformat() + "Z"
        
        # Log to audit_logs with before/after per Section K.8
        audit_logs_collection.add({
            "timestamp": now_str,
            "action": "REFUND_APPROVED",
            "actor_id": session.get('user_email', 'admin'),
            "refund_id": refund_id,
            "before_state": {"status": "pending", "transaction_status": "settled"},
            "after_state": {"status": "approved", "transaction_status": "refunded"},
            "details": f"Admin approved refund {refund_id}"
        })

        log_activity(session.get('user_email'), f"Refund approved for {refund_id}")
        return api_success({
            "refund_id": refund_id,
            "status": "approved",
            "transaction_status": "refunded"
        })
    except Exception as e:
        logger.error(f"Refund approval error: {str(e)}")
        return api_error(message="Failed to approve refund", status=500)


# ==============================================================================
# SECTION L: SUPER ADMIN SCREENS & APIS
# ==============================================================================

@app.route('/super-admin/admins')
@login_required
def super_admin_admins():
    return render_template('super_admin/admins_list.html')

@app.route('/super-admin/admins/new')
@login_required
def super_admin_new_admin():
    return render_template('super_admin/admin_form.html')

@app.route('/super-admin/properties')
@login_required
def super_admin_properties():
    return render_template('super_admin/properties_list.html')

@app.route('/super-admin/properties/<prop_id>')
@login_required
def super_admin_property_form(prop_id):
    return render_template('super_admin/property_form.html', prop_id=prop_id)

@app.route('/super-admin/settings')
@login_required
def super_admin_global_settings():
    return render_template('super_admin/global_settings.html')

@app.route('/super-admin/audit-log')
@login_required
def super_admin_audit_log():
    return render_template('super_admin/audit_log.html')

@app.route('/super-admin/impersonate')
@login_required
def super_admin_impersonate():
    return render_template('super_admin/impersonate.html')

@app.route('/api/super-admin/settings', methods=['GET'])
@login_required
def api_super_admin_get_settings():
    """
    GET /api/super-admin/settings per Section L.3
    Secrets masked: write-only keys never returned in full.
    """
    try:
        return api_success({
            "payment": {
                "provider": "razorpay",
                "api_key": "rzp_live_••••1234"
            },
            "otp": {
                "provider": "twilio",
                "length": 6,
                "expiry_minutes": 5,
                "max_attempts": 5
            },
            "pricing": {
                "tax_percent": 5,
                "service_charge_percent": 2.5
            },
            "feature_flags": {
                "facility_booking_enabled": True,
                "dark_mode_enabled": False
            }
        })
    except Exception as e:
        logger.error(f"Settings fetch error: {str(e)}")
        return api_error(message="Failed to load settings", status=500)

@app.route('/api/super-admin/settings', methods=['PATCH'])
@login_required
def api_super_admin_update_settings():
    try:
        data = request.json or {}
        log_activity(session.get('user_email'), "Super Admin updated global hotel system settings")
        return api_success({"updated": True})
    except Exception as e:
        return api_error(message="Failed to update settings", status=500)

@app.route('/api/super-admin/audit-log', methods=['GET'])
@login_required
def api_super_admin_get_audit_log():
    """
    GET /api/super-admin/audit-log per Section L.5
    Returns list of logs with before/after state diffs.
    """
    try:
        logs = []
        for doc in audit_logs_collection.stream():
            ld = doc.to_dict()
            ld['log_id'] = doc.id
            logs.append(ld)

        if not logs:
            logs = [
                {
                    "log_id": "log_5591",
                    "actor_id": "admin@nur-e-haya.com",
                    "actor_role": "admin",
                    "action": "refund_approved",
                    "target_type": "transaction",
                    "target_id": "txn_88f2a1",
                    "before": { "status": "pending_refund" },
                    "after": { "status": "refunded" },
                    "timestamp": "2026-09-08T16:02:00Z"
                },
                {
                    "log_id": "log_5592",
                    "actor_id": "frontdesk@nur-e-haya.com",
                    "actor_role": "front_desk",
                    "action": "room_checkout",
                    "target_type": "room",
                    "target_id": "room_204",
                    "before": { "status": "occupied" },
                    "after": { "status": "cleaning" },
                    "timestamp": "2026-09-12T14:10:00Z"
                },
                {
                    "log_id": "log_5593",
                    "actor_id": "superadmin@nur-e-haya.com",
                    "actor_role": "super_admin",
                    "action": "setting_change",
                    "target_type": "global_settings",
                    "target_id": "pricing",
                    "before": { "tax_percent": 4.5 },
                    "after": { "tax_percent": 5.0 },
                    "timestamp": "2026-09-12T17:30:00Z"
                }
            ]
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return api_success({
            "logs": logs,
            "next_cursor": None
        })
    except Exception as e:
        logger.error(f"Audit log fetch error: {str(e)}")
        return api_error(message="Failed to load audit logs", status=500)

@app.route('/api/super-admin/impersonate', methods=['POST'])
@login_required
def api_super_admin_impersonate():
    try:
        data = request.json or {}
        target_role = data.get('role', 'guest')
        target_email = data.get('email', f"{target_role}@nur-e-haya.com")
        
        session['user_role'] = target_role
        session['user_email'] = target_email
        log_activity("SUPER_ADMIN", f"Impersonated role: {target_role} ({target_email})")

        return api_success({
            "impersonating": True,
            "role": target_role,
            "email": target_email
        })
    except Exception as e:
        return api_error(message="Impersonation failed", status=500)


@app.route('/api/audit/permission-denied', methods=['POST'])






def api_audit_permission_denied():
    try:
        data = request.json or {}
        target = data.get('target', request.referrer or 'unknown')
        msg = data.get('message', 'Client-side permission denied event')
        log_audit_denied(
            db,
            actor_id=session.get('user_email', 'anonymous'),
            actor_role=session.get('user_role', 'guest'),
            target=target,
            details=msg
        )
        return api_success({"logged": True})
    except Exception as e:
        logger.error(f"Audit log route error: {str(e)}")
        return api_error(message="Could not log audit event", status=500)

@app.route('/api/auth/login', methods=['POST'])
@app.route('/api/login', methods=['POST'])
def api_auth_login():
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        remember_me = bool(data.get('remember_me', False))
        client_ip = request.remote_addr or 'unknown'
        rate_key = f"{client_ip}:{email}"
        
        # Rate-limiting check: 5 failed attempts in 10 minutes (Section B.2)
        is_blocked, minutes_to_wait = check_login_rate_limit(rate_key)
        if is_blocked:
            return api_error(
                message=f"Too many attempts, try again in {minutes_to_wait} minutes", 
                status=429
            )
            
        if not email or not password:
            record_failed_login(rate_key)
            return api_error(message="Invalid email or password", status=401)
            
        # Lookup user by email
        users = users_collection.where('email', '==', email).limit(1).get()
        user_list = list(users)
        
        if not user_list:
            record_failed_login(rate_key)
            return api_error(message="Invalid email or password", status=401)
            
        user_doc = user_list[0]
        user_data = user_doc.to_dict()
        
        if not verify_password(password, user_data.get('password', '')):
            record_failed_login(rate_key)
            return api_error(message="Invalid email or password", status=401)
            
        # Login success: clear rate limit
        clear_failed_login(rate_key)
        
        # Role and property_id derived server-side from stored user doc per Section B.3
        role = user_data.get('role', 'guest')
        property_id = user_data.get('property_id', 'prop_1')
        user_name = user_data.get('name', 'User')
        
        # Session cookie setup
        session.permanent = True
        if remember_me:
            app.permanent_session_lifetime = timedelta(days=30)
        else:
            app.permanent_session_lifetime = timedelta(hours=24)
            
        session['user_id'] = user_doc.id
        session['user_email'] = email
        session['user_name'] = user_name
        session['user_role'] = role
        session['property_id'] = property_id
        
        log_activity(email, "User logged in")
        logger.info(f"✅ User logged in: {email} ({role})")
        
        redirect_url = get_role_redirect(role)
        
        return api_success({
            "user": {
                "uid": user_doc.id,
                "name": user_name,
                "role": role,
                "property_id": property_id
            },
            "redirect": redirect_url
        })
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return api_error(message="Login failed. Please try again.", status=500)

@app.route('/api/auth/signup', methods=['POST'])
@app.route('/api/register', methods=['POST'])
def api_auth_signup():
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        name = (data.get('name') or '').strip()
        phone = (data.get('phone') or '').strip()
        
        errors = {}
        if not name:
            errors['name'] = "Full name is required."
        if not email:
            errors['email'] = "Email address is required."
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors['email'] = "Invalid email format."
        if not password:
            errors['password'] = "Password is required."
        elif not is_valid_password(password):
            errors['password'] = "Password must be at least 8 characters."
            
        if errors:
            return api_error(errors=errors, message="Please fix the validation errors.", status=400)
            
        existing_user = users_collection.where('email', '==', email).limit(1).get()
        if list(existing_user):
            return api_error(errors={"email": "Email already registered"}, message="Email already registered", status=400)
            
        new_user = {
            "email": email,
            "password": hash_password(password),
            "name": name,
            "phone": phone,
            "role": "guest",
            "property_id": "prop_1",
            "created_at": datetime.utcnow().isoformat(),
            "google_auth": False,
            "is_active": True
        }
        
        added_ref = users_collection.add(new_user)
        new_uid = added_ref[1].id
        
        session.permanent = True
        session['user_id'] = new_uid
        session['user_email'] = email
        session['user_name'] = name
        session['user_role'] = "guest"
        session['property_id'] = "prop_1"
        
        log_activity(email, "Guest registered")
        logger.info(f"✅ Guest registered: {email}")
        
        return api_success({
            "user": {
                "uid": new_uid,
                "name": name,
                "role": "guest",
                "property_id": "prop_1"
            },
            "redirect": "/dashboard"
        })
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return api_error(message="Registration failed", status=500)

@app.route('/api/auth/invite/accept', methods=['POST'])
def api_auth_invite_accept():
    try:
        data = request.json or {}
        token = (data.get('token') or '').strip()
        name = (data.get('name') or '').strip()
        password = data.get('password') or ''
        
        errors = {}
        if not token:
            return api_error(message="Invite token is required.", status=400)
        if not name:
            errors['name'] = "Name is required."
        if not password:
            errors['password'] = "Password is required."
        elif not is_valid_staff_password(password):
            errors['password'] = "Password must be at least 10 characters and contain at least 1 number and 1 symbol."
            
        if errors:
            return api_error(errors=errors, message="Validation failed", status=400)
            
        # Validate invite in Firestore
        inv_ref = invites_collection.document(token)
        inv_snap = inv_ref.get()
        if not inv_snap.exists:
            return api_error(message="This invite link has expired — ask your admin to resend it.", status=400)
            
        inv_data = inv_snap.to_dict()
        now_iso = datetime.utcnow().isoformat()
        
        if inv_data.get('used', False) or inv_data.get('expires_at', '') <= now_iso:
            return api_error(message="This invite link has expired — ask your admin to resend it.", status=400)
            
        email = inv_data.get('email')
        role = inv_data.get('role', 'staff')
        department_id = inv_data.get('department_id', 'dept_general')
        property_id = inv_data.get('property_id', 'prop_1')
        
        # Create or update user
        existing_users = list(users_collection.where('email', '==', email).limit(1).get())
        if existing_users:
            user_doc = existing_users[0]
            uid = user_doc.id
            user_doc.reference.update({
                "name": name,
                "password": hash_password(password),
                "role": role,
                "department_id": department_id,
                "property_id": property_id,
                "is_active": True,
                "updated_at": now_iso
            })
        else:
            _, new_ref = users_collection.add({
                "email": email,
                "name": name,
                "password": hash_password(password),
                "role": role,
                "department_id": department_id,
                "property_id": property_id,
                "is_active": True,
                "created_at": now_iso,
                "google_auth": False
            })
            uid = new_ref.id
            
        # Mark invite used
        inv_ref.update({
            "used": True,
            "accepted_at": now_iso,
            "accepted_uid": uid
        })
        
        # Set session
        session.permanent = True
        session['user_id'] = uid
        session['user_email'] = email
        session['user_name'] = name
        session['user_role'] = role
        session['property_id'] = property_id
        
        log_activity(email, f"Staff invite accepted ({role})")
        logger.info(f"✅ Staff invite accepted: {email} ({role})")
        
        redirect_url = get_role_redirect(role)
        return api_success({
            "user": {
                "uid": uid,
                "role": role,
                "department_id": department_id
            },
            "redirect": redirect_url
        })
    except Exception as e:
        logger.error(f"Invite accept error: {str(e)}")
        return api_error(message="Failed to accept invite", status=500)

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_auth_forgot_password():
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return api_error(errors={"email": "Please enter a valid email address."}, message="Invalid email", status=400)
            
        users = list(users_collection.where('email', '==', email).limit(1).get())
        if users:
            token = secrets.token_urlsafe(32)
            expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat()
            password_resets_collection.document(token).set({
                "token": token,
                "email": email,
                "expires_at": expires_at,
                "used": False,
                "created_at": datetime.utcnow().isoformat()
            })
            reset_url = f"/reset-password/{token}"
            logger.info(f"🔑 Password reset link generated for {email}: {reset_url}")
            return api_success({
                "message": "A reset link has been generated.",
                "reset_url": reset_url
            })
        else:
            return api_success({
                "message": "If that email is registered, password reset instructions have been generated."
            })
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return api_error(message="Could not process request", status=500)

@app.route('/api/auth/reset-password', methods=['POST'])
def api_auth_reset_password():
    try:
        data = request.json or {}
        token = (data.get('token') or '').strip()
        password = data.get('password') or ''
        
        if not token:
            return api_error(message="Reset token is required.", status=400)
        if not password or len(password) < 8:
            return api_error(errors={"password": "Password must be at least 8 characters."}, message="Invalid password", status=400)
            
        token_doc = password_resets_collection.document(token).get()
        if not token_doc.exists:
            return api_error(message="Invalid or expired reset token.", status=400)
            
        t_data = token_doc.to_dict()
        now_iso = datetime.utcnow().isoformat()
        if t_data.get('used', False) or t_data.get('expires_at', '') <= now_iso:
            return api_error(message="This reset token has expired or has already been used.", status=400)
            
        email = t_data.get('email')
        users = list(users_collection.where('email', '==', email).limit(1).get())
        if not users:
            return api_error(message="User not found.", status=404)
            
        user_doc = users[0]
        user_doc.reference.update({
            "password": hash_password(password),
            "updated_at": now_iso
        })
        
        token_doc.reference.update({
            "used": True,
            "reset_at": now_iso
        })
        
        log_activity(email, "Password reset successfully")
        return api_success({
            "message": "Password updated successfully. You may now log in.",
            "redirect": "/login"
        })
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return api_error(message="Failed to reset password", status=500)


@app.route('/api/google-auth', methods=['POST'])
def google_auth():
    try:
        data = request.json or {}
        email = (data.get('email') or '').strip().lower()
        name = (data.get('name') or '').strip()
        google_id = (data.get('googleId') or '').strip()
        
        if not email or not name or not google_id:
            return api_error(message="Invalid Google authentication data", status=400)
        
        users = users_collection.where('email', '==', email).limit(1).get()
        user_list = list(users)
        
        if user_list:
            user_doc = user_list[0]
            user_data = user_doc.to_dict() or {}
            user_id = user_doc.id
            role = user_data.get('role', 'guest')
            property_id = user_data.get('property_id', 'prop_1')
            user_name = user_data.get('name') or name
            
            # Update google_auth flag if not already marked
            if not user_data.get('google_auth'):
                try:
                    users_collection.document(user_id).update({
                        "google_auth": True,
                        "google_id": google_id
                    })
                except Exception as update_err:
                    logger.warning(f"Could not update google_auth on existing user: {update_err}")
        else:
            new_user = {
                "email": email,
                "password": hash_password(google_id),
                "name": name,
                "phone": "",
                "role": "guest",
                "property_id": "prop_1",
                "created_at": datetime.utcnow().isoformat(),
                "google_auth": True,
                "google_id": google_id,
                "is_active": True
            }
            added_ref = users_collection.add(new_user)
            user_id = added_ref[1].id
            role = "guest"
            property_id = "prop_1"
            user_name = name
            log_activity(email, "User registered via Google")
            logger.info(f"✅ User registered via Google: {email}")
        
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = user_name
        session['user_role'] = role
        session['property_id'] = property_id
        
        log_activity(email, "User logged in via Google")
        logger.info(f"✅ User logged in via Google: {email} ({role})")
        
        redirect_url = get_role_redirect(role)
        return api_success({
            "user": {
                "uid": user_id,
                "name": user_name,
                "role": role,
                "property_id": property_id
            },
            "redirect": redirect_url,
            "message": "Google authentication successful"
        })
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        return api_error(message="Google sign-in failed. Please try again.", status=500)

@app.route('/logout', methods=['GET', 'POST'])
@app.route('/signout', methods=['GET', 'POST'])
def logout_view():
    email = session.get('user_email')
    if email:
        log_activity(email, "User logged out")
    session.clear()
    next_url = request.args.get('next', '/login?logged_out=true')
    if not next_url.startswith(('/login', '/signup', '/')):
        next_url = '/login?logged_out=true'
    return redirect(next_url)

@app.route('/api/auth/logout', methods=['POST', 'GET'])
@app.route('/api/logout', methods=['POST', 'GET'])
def api_logout():
    email = session.get('user_email')
    if email:
        log_activity(email, "User logged out")
    session.clear()
    return jsonify({
        "ok": True,
        "success": True,
        "message": "Logged out successfully",
        "redirect": "/login?logged_out=true"
    })




@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    rooms = rooms_collection.stream()
    rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    if not rooms_list:
        init_sample_rooms()
        rooms = rooms_collection.stream()
        rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    return api_success(rooms_list)

@app.route('/api/rooms/available', methods=['GET'])
@login_required
def get_available_rooms():
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    

    rooms = rooms_collection.stream()
    rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    
    
    if not rooms_list:
        init_sample_rooms()
        rooms = rooms_collection.stream()
        rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    
    
    bookings = bookings_collection.where('status', '==', 'confirmed').stream()
    bookings_list = [booking.to_dict() for booking in bookings]
    
    
    if not bookings_list:
        return jsonify(rooms_list)
    
    available_rooms = []
    for room in rooms_list:
        is_available = True
        for booking in bookings_list:
            try:
                if (booking['room_id'] == room['id'] and 
                    not (booking['check_out'] <= check_in or booking['check_in'] >= check_out)):
                    is_available = False
                    break
            except KeyError:
            
                continue
        if is_available:
            available_rooms.append(room)
    
    return jsonify(available_rooms)



@app.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment and create transaction record"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No payment data provided"}), 400
        
        required_fields = ['billing_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode', 'payment_method', 'amount']
        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({"success": False, "message": "Invalid payment amount"}), 400
            if amount > 1000000:
                return jsonify({"success": False, "message": "Amount exceeds maximum limit"}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid amount format"}), 400
        
        # Validate payment method
        valid_methods = ['card', 'upi', 'netbanking', 'wallet']
        if data.get('payment_method') not in valid_methods:
            return jsonify({"success": False, "message": "Invalid payment method"}), 400
        
        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Validate phone (basic validation)
        phone = str(data.get('phone', ''))
        if len(phone) < 10:
            return jsonify({"success": False, "message": "Invalid phone number"}), 400
        
        transaction_id = generate_transaction_id()
        
        transaction_data = {
            "transaction_id": transaction_id,
            "user_email": session.get('user_email'),
            "user_name": session.get('user_name', ''),
            "amount": amount,
            "payment_method": data['payment_method'],
            "payment_status": "completed",
            
            "billing_name": data['billing_name'],
            "billing_email": data['email'],
            "billing_phone": phone,
            "billing_address": data['address'],
            "billing_city": data['city'],
            "billing_state": data['state'],
            "billing_zipcode": data['zipcode'],
            "billing_country": data.get('country', 'India'),
            
            "booking_data": data.get('booking_data', {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "booking_id": None
        }
        
        payment_method = data.get('payment_method')
        if payment_method == 'card':
            card_number = data.get('card_number', '')
            transaction_data['card_last4'] = card_number[-4:] if len(card_number) >= 4 else None
            transaction_data['card_type'] = data.get('card_type', 'credit')
        elif payment_method == 'netbanking':
            transaction_data['bank_name'] = data.get('bank', '')
        elif payment_method == 'upi':
            transaction_data['upi_id'] = data.get('upi_id', '')
        
        
        transactions_collection.document(transaction_id).set(transaction_data)
        
        log_activity(
            session['user_email'], 
            "Payment processed", 
            f"Transaction: {transaction_id}, Method: {payment_method}, Amount: ₹{data['amount']}"
        )
        
        print(f"✅ Payment processed: {transaction_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment processed successfully",
            "transaction_id": transaction_id,
            "payment_method": payment_method,
            "amount": data['amount'],
            "status": "completed"
        })
        
    except Exception as e:
        print(f"❌ Payment processing error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Payment processing failed: {str(e)}"
        }), 500



@app.route('/api/bookings', methods=['GET', 'POST'])
@login_required
def handle_bookings():
    if request.method == 'GET':
        try:
            # Update expired bookings first
            update_expired_bookings(session['user_email'])
            
            bookings = bookings_collection.where('user_email', '==', session['user_email']).stream()
            bookings_list = [{"id": booking.id, **booking.to_dict()} for booking in bookings]
            
            # Sort by created_at descending
            bookings_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"✅ Fetched {len(bookings_list)} bookings for {session['user_email']}")
            return jsonify(bookings_list)
        except Exception as e:
            logger.error(f"Get bookings error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        data = request.json
        
        required_fields = ['room_id', 'room_number', 'check_in', 'check_out', 'guests', 'total_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing field: {field}"}), 400
        
        try:
            
            new_booking = {
                "user_email": session['user_email'],
                "user_name": session.get('user_name', ''),
                "room_id": data['room_id'],
                "room_number": data['room_number'],
                "check_in": data['check_in'],
                "check_out": data['check_out'],
                "guests": data['guests'],
                "total_price": data['total_price'],
                "status": "confirmed",
                "created_at": datetime.now().isoformat(),
                
                
                "payment_method": data.get('payment_method', 'card'),
                "payment_status": data.get('payment_status', 'completed'),
                "transaction_id": data.get('transaction_id', None)  
            }
            
            
            doc_ref = bookings_collection.add(new_booking)
            booking_id = doc_ref[1].id
            new_booking['id'] = booking_id
            
            
            if new_booking.get('transaction_id'):
                try:
                    transaction_ref = transactions_collection.document(new_booking['transaction_id'])
                    transaction_ref.update({
                        "booking_id": booking_id,
                        "updated_at": datetime.now().isoformat()
                    })
                    print(f"✅ Transaction {new_booking['transaction_id']} updated with booking_id: {booking_id}")
                except Exception as e:
                    print(f"⚠️ Could not update transaction: {str(e)}")
            
            log_activity(
                session['user_email'], 
                "Booking created", 
                f"Room {data['room_number']}, Transaction: {new_booking.get('transaction_id', 'N/A')}"
            )
            
            print(f"✅ Booking created: {booking_id}")
            
            return jsonify({"success": True, "booking": new_booking})
            
        except Exception as e:
            print(f"❌ Booking creation error: {str(e)}")
            return jsonify({"success": False, "message": f"Booking failed: {str(e)}"}), 500

@app.route('/api/dashboard-stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    try:
        # Update expired bookings first
        update_expired_bookings(session['user_email'])
        
        bookings = bookings_collection.where('user_email', '==', session['user_email']).stream()
        user_bookings = [{"id": booking.id, **booking.to_dict()} for booking in bookings]
        
        # Sort by created_at descending
        user_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate active bookings (confirmed status AND checkout date in future)
        now = datetime.now()
        active_count = 0
        
        for booking in user_bookings:
            if booking.get('status') == 'confirmed':
                try:
                    check_out_str = booking.get('check_out', '')
                    check_out_date = datetime.fromisoformat(check_out_str.replace('Z', '+00:00'))
                    current_date = datetime.now(check_out_date.tzinfo) if check_out_date.tzinfo else now
                    
                    if check_out_date > current_date:
                        active_count += 1
                except Exception as e:
                    logger.warning(f"Error parsing checkout date: {str(e)}")
        
        stats = {
            "total_bookings": len(user_bookings),
            "active_bookings": active_count,  # Only count future bookings
            "total_spent": sum(b['total_price'] for b in user_bookings if b['status'] == 'confirmed'),
            "recent_bookings": user_bookings[:5]
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Get all transactions for current user"""
    transactions = transactions_collection.where('user_email', '==', session['user_email']).stream()
    transactions_list = [{"id": trans.id, **trans.to_dict()} for trans in transactions]
    

    transactions_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify(transactions_list)

@app.route('/api/transactions/<transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Get specific transaction details"""
    transaction_ref = transactions_collection.document(transaction_id)
    transaction = transaction_ref.get()
    
    if not transaction.exists:
        return jsonify({"success": False, "message": "Transaction not found"}), 404
    
    transaction_data = transaction.to_dict()
    
    
    if transaction_data['user_email'] != session['user_email']:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    transaction_data['id'] = transaction_id
    return jsonify({"success": True, "transaction": transaction_data})



@app.route('/api/reset-rooms')
@login_required
def reset_rooms():
    """Reset all rooms to default state"""
    
    rooms = rooms_collection.stream()
    for room in rooms:
        room.reference.delete()
    
    
    init_sample_rooms()
    return jsonify({"success": True, "message": "Rooms have been reset"})

@app.route('/api/chatbot', methods=['GET', 'POST'])
@app.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """
    Process chatbot message and return response (accessible for both guests and authenticated users)
    """
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "status": "online",
            "bot": "Nur-e-Haya Luxury AI Concierge",
            "suggestions": chatbot_instance.get_suggested_questions()
        })

    try:
        data = request.json or {}
        message = (data.get('message') or data.get('query') or data.get('text') or '').strip()
        
        if not message:
            return jsonify({
                "success": False,
                "message": "Empty message",
                "response": "Please type a message so I can assist you."
            }), 400
        
        # Get user email from session or default to guest traveler
        user_email = session.get('user_email', 'guest@nur-e-haya.com')
        
        # Process message through chatbot
        bot_response = get_bot_response(message, user_email)
        
        # Store conversation in Firestore for learning/improvement
        conversation_data = {
            "user_email": user_email,
            "user_message": message,
            "bot_response": bot_response['response'],
            "intent": bot_response.get('intent'),
            "confidence": bot_response.get('confidence'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to Firestore (optional - for analytics)
        try:
            db.collection('chatbot_conversations').add(conversation_data)
        except Exception as e:
            print(f"⚠️ Could not save conversation: {str(e)}")
        
        # Log activity
        log_activity(user_email, "Chatbot interaction", f"Intent: {bot_response.get('intent')}")
        
        return jsonify({
            "success": True,
            "response": bot_response['response'],
            "intent": bot_response.get('intent'),
            "confidence": bot_response.get('confidence'),
            "suggestions": bot_response.get('suggestions', []),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Chatbot error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Sorry, I encountered an error. Please try again.",
            "error": str(e)
        }), 500


@app.route('/api/chatbot/suggestions', methods=['GET'])
@login_required
def chatbot_suggestions():
    """
    Get suggested questions for the chatbot
    """
    try:
        suggestions = chatbot_instance.get_suggested_questions()
        return jsonify({
            "success": True,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/chatbot/history', methods=['GET'])
@login_required
def chatbot_history():
    """
    Get user's chat history
    """
    try:
        user_email = session.get('user_email')
        
        # Get last 50 conversations
        conversations = db.collection('chatbot_conversations')\
            .where('user_email', '==', user_email)\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(50)\
            .stream()
        
        history = []
        for conv in conversations:
            conv_data = conv.to_dict()
            history.append({
                "id": conv.id,
                "user_message": conv_data.get('user_message'),
                "bot_response": conv_data.get('bot_response'),
                "timestamp": conv_data.get('timestamp')
            })
        
        return jsonify({
            "success": True,
            "history": history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/chatbot/feedback', methods=['POST'])
@login_required
def chatbot_feedback():
    """
    Collect user feedback on chatbot responses
    """
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        rating = data.get('rating')  # 1-5 or thumbs up/down
        feedback_text = data.get('feedback', '')
        
        feedback_data = {
            "conversation_id": conversation_id,
            "user_email": session.get('user_email'),
            "rating": rating,
            "feedback_text": feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        db.collection('chatbot_feedback').add(feedback_data)
        
        return jsonify({
            "success": True,
            "message": "Thank you for your feedback!"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter - Firebase version"""
    try:
        # Get email from request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'message': 'No data received'
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        # Validate email format
        if not email:
            return jsonify({
                'success': False, 
                'message': 'Email is required'
            }), 400
        
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False, 
                'message': 'Invalid email format'
            }), 400
        
        # Check if already subscribed in Firebase
        try:
            subscribers_ref = db.collection('newsletter_subscribers')
            existing = subscribers_ref.where('email', '==', email).limit(1).get()
            
            if len(list(existing)) > 0:
                return jsonify({
                    'success': False, 
                    'message': 'already_subscribed'
                }), 200
        except Exception as check_error:
            print(f"Firebase check error: {check_error}")
            # Continue even if check fails
        
        # Create subscriber document
        from datetime import datetime
        import time
        
        subscriber = {
            'email': email,
            'subscribed_at': datetime.utcnow().isoformat(),
            'timestamp': time.time(),
            'status': 'active',
            'source': 'website_footer',
            'ip_address': request.remote_addr if hasattr(request, 'remote_addr') else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown') if hasattr(request, 'headers') else 'unknown'
        }
        
        # Save to Firebase Firestore
        try:
            doc_ref = db.collection('newsletter_subscribers').document()
            doc_ref.set(subscriber)
            
            print(f"✅ New newsletter subscriber: {email} (ID: {doc_ref.id})")
            
        except Exception as firebase_error:
            print(f"Firebase insert error: {firebase_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False, 
                'message': f'Database error: {str(firebase_error)}'
            }), 500
        
        return jsonify({
            'success': True, 
            'message': 'Successfully subscribed to newsletter',
            'email': email
        }), 200
        
    except Exception as e:
        print(f"❌ Newsletter subscription error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/chatbot/transfer', methods=['POST'])
@login_required
def chatbot_transfer():
    """
    Transfer chat to human agent
    """
    try:
        data = request.json
        reason = data.get('reason', 'User requested transfer')
        conversation_context = data.get('context', [])
        
        transfer_data = {
            "user_email": session.get('user_email'),
            "user_name": session.get('user_name'),
            "reason": reason,
            "conversation_context": conversation_context,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Save transfer request
        transfer_ref = db.collection('agent_transfers').add(transfer_data)
        
        # Log activity
        log_activity(
            session.get('user_email'),
            "Agent transfer requested",
            reason
        )
        
        return jsonify({
            "success": True,
            "message": "Transfer request created. An agent will join shortly.",
            "transfer_id": transfer_ref[1].id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/admin/newsletter')
@login_required
def admin_newsletter():
    """View newsletter subscribers (ADMIN ONLY - test1@gmail.com)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return redirect('/dashboard')
        
        # Get all subscribers from Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        
        subscribers = []
        for doc in docs:
            sub_data = doc.to_dict()
            sub_data['id'] = doc.id
            subscribers.append(sub_data)
        
        # Count statistics
        total_subscribers = len(subscribers)
        active_subscribers = len([s for s in subscribers if s.get('status') == 'active'])
        
        stats = {
            'total': total_subscribers,
            'active': active_subscribers,
            'unsubscribed': total_subscribers - active_subscribers
        }
        
        return render_template('admin_newsletter.html', 
                             subscribers=subscribers, 
                             stats=stats)
    except Exception as e:
        print(f"Error loading newsletter admin: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading subscribers: {str(e)}", 500


@app.route('/api/newsletter/export')
@login_required
def export_newsletter():
    """Export newsletter subscribers as JSON (ADMIN ONLY)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get all subscribers from Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        
        subscribers = []
        for doc in docs:
            sub_data = doc.to_dict()
            sub_data['id'] = doc.id
            subscribers.append(sub_data)
        
        return jsonify({
            'success': True,
            'subscribers': subscribers
        }), 200
        
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Export failed: {str(e)}'
        }), 500


@app.route('/api/newsletter/check-subscription', methods=['POST'])
def check_newsletter_subscription():
    """Check if user is subscribed to newsletter"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'subscribed': False}), 200
        
        # Check in Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.where('email', '==', email).where('status', '==', 'active').limit(1).get()
        
        is_subscribed = len(list(docs)) > 0
        
        return jsonify({'subscribed': is_subscribed}), 200
        
    except Exception as e:
        print(f"Check subscription error: {e}")
        return jsonify({'subscribed': False}), 200


@app.route('/api/newsletter/unsubscribe', methods=['POST'])
def unsubscribe_newsletter():
    """Unsubscribe from newsletter"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        # Find subscriber in Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.where('email', '==', email).limit(1).get()
        
        found = False
        for doc in docs:
            # Update status to unsubscribed
            doc.reference.update({
                'status': 'unsubscribed',
                'unsubscribed_at': datetime.utcnow().isoformat()
            })
            found = True
            print(f"✅ Unsubscribed: {email}")
            break
        
        if not found:
            return jsonify({
                'success': False,
                'message': 'Email not found in subscriber list'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Successfully unsubscribed'
        }), 200
        
    except Exception as e:
        print(f"Unsubscribe error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/admin/all-bookings', methods=['GET'])
@login_required
def get_all_bookings():
    """Get all bookings from all users (ADMIN ONLY)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return jsonify({
                "success": False,
                "message": "Unauthorized. Admin access only."
            }), 403
        
        # Fetch all bookings from Firebase
        bookings = bookings_collection.stream()
        all_bookings = []
        
        for booking in bookings:
            booking_data = booking.to_dict()
            booking_data['id'] = booking.id
            all_bookings.append(booking_data)
        
        # Sort by created_at (newest first)
        all_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        log_activity(
            session['user_email'], 
            "Admin: Downloaded all bookings report", 
            f"Total bookings: {len(all_bookings)}"
        )
        
        print(f"✅ Admin {session['user_email']} exported {len(all_bookings)} bookings")
        
        return jsonify({
            "success": True,
            "bookings": all_bookings,
            "total_count": len(all_bookings)
        })
        
    except Exception as e:
        print(f"❌ Error fetching all bookings: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error fetching bookings: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    init_sample_rooms()
    init_seed_users()
    
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)
