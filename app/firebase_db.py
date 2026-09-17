import os
import sys
import json
import base64
import logging
from unittest.mock import MagicMock

# CRITICAL protobuf setting before google imports
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

logger = logging.getLogger(__name__)

import time
import random
import copy
from datetime import datetime

class MockDocumentSnapshot:
    def __init__(self, doc_id, data, exists, reference):
        self.id = str(doc_id)
        self._data = copy.deepcopy(data) if data is not None else {}
        self.exists = exists
        self.reference = reference

    def to_dict(self):
        return copy.deepcopy(self._data) if self.exists else None

class MockDocumentReference:
    def __init__(self, collection, doc_id):
        self._collection = collection
        self.id = str(doc_id)

    def get(self):
        exists = self.id in self._collection._docs
        data = self._collection._docs.get(self.id)
        return MockDocumentSnapshot(self.id, data, exists, self)

    def set(self, data, merge=False):
        d = copy.deepcopy(data)
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(d)
        else:
            self._collection._docs[self.id] = d

    def update(self, data):
        if self.id not in self._collection._docs:
            try:
                from google.cloud.exceptions import NotFound
                raise NotFound(f"No document to update: {self.id}")
            except ImportError:
                raise KeyError(f"No document to update: {self.id}")
        self._collection._docs[self.id].update(copy.deepcopy(data))

    def delete(self):
        self._collection._docs.pop(self.id, None)

class MockQuery:
    def __init__(self, collection, filters=None, limit_num=None, order_field=None, order_desc=False):
        self._collection = collection
        self._filters = filters or []
        self._limit_num = limit_num
        self._order_field = order_field
        self._order_desc = order_desc

    def where(self, field_path=None, op_string=None, value=None, filter=None):
        new_filters = list(self._filters)
        if field_path is not None and op_string is not None:
            new_filters.append((field_path, op_string, value))
        elif filter is not None:
            new_filters.append((getattr(filter, 'field_path', ''), getattr(filter, 'op_string', '=='), getattr(filter, 'value', None)))
        return MockQuery(self._collection, new_filters, self._limit_num, self._order_field, self._order_desc)

    def limit(self, n):
        return MockQuery(self._collection, self._filters, n, self._order_field, self._order_desc)

    def order_by(self, field, direction=None):
        desc = (direction == 'DESCENDING' or str(direction).lower() == 'desc')
        return MockQuery(self._collection, self._filters, self._limit_num, field, desc)

    def _matches(self, doc_data):
        for field, op, val in self._filters:
            actual = doc_data.get(field)
            if op == '==':
                if actual != val and str(actual) != str(val):
                    return False
            elif op == '!=':
                if actual == val or str(actual) == str(val):
                    return False
            elif op == 'in':
                if val is None or actual not in val:
                    return False
            elif op == '>=':
                if actual is None or actual < val:
                    return False
            elif op == '<=':
                if actual is None or actual > val:
                    return False
            elif op == '>':
                if actual is None or actual <= val:
                    return False
            elif op == '<':
                if actual is None or actual >= val:
                    return False
        return True

    def get(self):
        return list(self.stream())

    def stream(self):
        results = []
        for doc_id, data in list(self._collection._docs.items()):
            if self._matches(data):
                results.append(MockDocumentSnapshot(doc_id, data, True, MockDocumentReference(self._collection, doc_id)))
        if self._order_field:
            results.sort(key=lambda s: s.to_dict().get(self._order_field, '') or '', reverse=self._order_desc)
        if self._limit_num is not None:
            results = results[:self._limit_num]
        return iter(results)

class MockCollectionReference(MockQuery):
    def __init__(self, name, db=None):
        self.name = name
        self._docs = {}
        self._db = db
        self._client = db
        super().__init__(self)

    def document(self, doc_id=None):
        if not doc_id:
            doc_id = f"doc_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        return MockDocumentReference(self, str(doc_id))

    def add(self, data):
        doc_id = f"doc_{int(time.time() * 1000)}_{random.randint(100, 999)}"
        ref = self.document(doc_id)
        ref.set(data)
        now_ts = datetime.utcnow()
        return (now_ts, ref)

class InMemoryFirestore:
    def __init__(self):
        self._collections = {}
        self._init_defaults()

    def collection(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollectionReference(name, db=self)
        return self._collections[name]

    def _init_defaults(self):
        # Default settings
        self.collection('settings').document('general').set({
            "hotel_name": "Nur-e-Haya Luxury Palace",
            "currency": "INR",
            "phone": "+91 98765 43210",
            "email": "concierge@nur-e-haya.com",
            "rzp_key_secret": "sec_live_999",
            "stripe_secret_key": "sk_live_999",
            "tax_rate": 18
        })

        # Default promo codes
        promos = [
            {"code": "ROYAL50", "discount_percent": 50, "is_active": True},
            {"code": "WELCOME10", "discount_percent": 10, "is_active": True},
            {"code": "MEMBER20", "discount_percent": 20, "is_active": True},
        ]
        p_col = self.collection('promo_codes')
        for p in promos:
            p_col.document(p['code']).set(p)

        # Default facilities
        facs = [
            {"name": "Royal Ayur Spa", "category": "Wellness", "price": 2500, "status": "active"},
            {"name": "Infinity Pool", "category": "Recreation", "price": 1000, "status": "active"},
        ]
        f_col = self.collection('facilities')
        for i, f in enumerate(facs, 1):
            f_col.document(f"fac_{i}").set(f)

        # Seed 150+ menu items, 40+ rooms, 24 tables via data_seeder
        try:
            from data_seeder import seed_all_data
            seed_all_data(db_client=self)
        except Exception as e:
            logger.warning(f"Error seeding mock database: {e}")

        # Seed standard users for all roles
        try:
            from app.auth.routes import init_seed_users
            init_seed_users()
        except Exception as e:
            logger.warning(f"Error seeding default users: {e}")

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
        _db = InMemoryFirestore()
        
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
def staff_invites_col(): return invites_col()
def password_resets_col(): return get_collection('password_resets')
def logs_col(): return get_collection('logs')
def chat_history_col(): return get_collection('chat_history')


def resolve_room_doc(room_identifier):
    """
    Resolves any room identifier (canonical ID, flat_code, number, etc.) to the
    single canonical room document snapshot/reference.
    Eliminates the duplicate-document ambiguity (Part 0.1).
    """
    if not room_identifier:
        return None

    col = rooms_col()
    r_str = str(room_identifier).strip()

    # 1. Direct document ID lookup
    doc = col.document(r_str).get()
    if doc.exists:
        return doc

    # 2. Try prefixed canonical patterns (e.g. 'rm_HW-101', 'rm_101')
    candidates = [
        f"rm_{r_str}",
        f"room_{r_str}"
    ]
    for c in candidates:
        d = col.document(c).get()
        if d.exists:
            return d

    # 3. Query by fields: flat_code, number, flat_no, id
    for f in ['flat_code', 'number', 'flat_no', 'id']:
        matches = list(col.where(f, '==', r_str).limit(1).get())
        if matches and matches[0].exists:
            return matches[0]

    # 4. If numeric part was passed, try matching number
    num_part = ''.join(filter(str.isdigit, r_str))
    if num_part and num_part != r_str:
        matches = list(col.where('number', '==', num_part).limit(1).get())
        if matches and matches[0].exists:
            return matches[0]

    return None


def resolve_menu_item_doc(item_id):
    """
    Resolves menu item identifier (e.g. 'item_1', 'item_001', numeric '1')
    to its canonical document snapshot. (Part 0.3)
    """
    if not item_id:
        return None
    col = menu_col()
    i_str = str(item_id).strip()

    # 1. Direct document lookup
    doc = col.document(i_str).get()
    if doc.exists:
        return doc

    # 2. Try unpadded and zero-padded variants
    num_part = ''.join(filter(str.isdigit, i_str))
    if num_part:
        val = int(num_part)
        for variant in [f"item_{val}", f"item_{val:03d}", f"item_{val:02d}"]:
            d = col.document(variant).get()
            if d.exists:
                return d

    # 3. Field query
    for f in ['id', 'name']:
        matches = list(col.where(f, '==', i_str).limit(1).get())
        if matches and matches[0].exists:
            return matches[0]

    return None

