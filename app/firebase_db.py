import os
import sys
import json
import base64
import logging
from unittest.mock import MagicMock

# CRITICAL protobuf setting before google imports
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

logger = logging.getLogger(__name__)

_db = None

def get_db():
    """Returns the initialized Firestore database client or creates it if needed"""
    global _db
    if _db is not None:
        return _db
        
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
        firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
        firebase_creds_base64 = os.getenv('FIREBASE_CREDENTIALS_BASE64')
        
        cred = None
        if os.path.exists(firebase_creds_path):
            cred = credentials.Certificate(firebase_creds_path)
        elif firebase_creds_json:
            cred = credentials.Certificate(json.loads(firebase_creds_json))
        elif firebase_creds_base64:
            decoded_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
            cred = credentials.Certificate(json.loads(decoded_json))
        else:
            raise FileNotFoundError(f"Firebase credentials not found at {firebase_creds_path}")
            
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        _db = firestore.client()
        logger.info("✅ Firebase Firestore initialized successfully via app/firebase_db.py")
    except Exception as e:
        if os.getenv('FLASK_ENV') == 'production':
            logger.error(f"❌ Production Firebase initialization failed: {str(e)}")
            raise
        logger.warning(f"⚠️ Firebase initialization skipped/mocked in non-production mode: {str(e)}")
        _db = MagicMock(name='mock_firestore_db')
        
    return _db

# Collection Helper Functions
def get_collection(name: str):
    return get_db().collection(name)

def users_col(): return get_collection('users')
def otp_codes_col(): return get_collection('otp_codes')
def rooms_col(): return get_collection('rooms')
def bookings_col(): return get_collection('bookings')
def menu_col(): return get_collection('menu_items')
def orders_col(): return get_collection('orders')
def service_requests_col(): return get_collection('service_requests')
def tasks_col(): return get_collection('tasks')
def housekeeping_tasks_col(): return get_collection('housekeeping_tasks')
def laundry_tasks_col(): return get_collection('laundry_tasks')
def maintenance_tickets_col(): return get_collection('maintenance_tickets')
def maintenance_orders_col(): return get_collection('maintenance_orders')
def assets_col(): return get_collection('assets')
def concierge_requests_col(): return get_collection('concierge_requests')
def transactions_col(): return get_collection('transactions')
def invoices_col(): return get_collection('invoices')
def qr_payments_col(): return get_collection('qr_payments')
def refunds_col(): return get_collection('refunds')
def inventory_col(): return get_collection('inventory')
def banquet_bookings_col(): return get_collection('banquet_bookings')
def catering_packages_col(): return get_collection('catering_packages')
def spa_bookings_col(): return get_collection('spa_bookings')
def pool_bookings_col(): return get_collection('pool_bookings')
def gym_bookings_col(): return get_collection('gym_bookings')
def visitor_logs_col(): return get_collection('visitor_logs')
def security_incidents_col(): return get_collection('security_incidents')
def parking_records_col(): return get_collection('parking_records')
def reviews_col(): return get_collection('reviews')
def promo_codes_col(): return get_collection('promo_codes')
def loyalty_points_log_col(): return get_collection('loyalty_points_log')
def notifications_col(): return get_collection('notifications')
def announcements_col(): return get_collection('announcements')
def audit_logs_col(): return get_collection('audit_logs')
def settings_col(): return get_collection('settings')
def night_audits_col(): return get_collection('night_audits')
def facilities_col(): return get_collection('facilities')
def lost_found_col(): return get_collection('lost_found')
def linen_col(): return get_collection('linen')
def restaurant_tables_col(): return get_collection('restaurant_tables')
def mini_bar_orders_col(): return get_collection('mini_bar_orders')
def invites_col(): return get_collection('invites')
def password_resets_col(): return get_collection('password_resets')
def logs_col(): return get_collection('logs')
