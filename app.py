# app.py - Main Entry Point for Nur-e-Haya Hotel Management System
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

from app import create_app
from app.firebase_db import (
    get_db, users_col, rooms_col, bookings_col, transactions_col,
    logs_col, audit_logs_col, invites_col, password_resets_col,
    facilities_col, menu_col, housekeeping_tasks_col, maintenance_tickets_col,
    laundry_tasks_col, orders_col, security_incidents_col
)
from app.auth.routes import (
    is_valid_password, is_valid_staff_password,
    check_login_rate_limit, record_failed_login, clear_failed_login,
    get_role_redirect, hash_password, verify_password
)

app = create_app()

# Expose Firestore collections for backwards compatibility with legacy tests
db = get_db()
users_collection = users_col()
rooms_collection = rooms_col()
bookings_collection = bookings_col()
transactions_collection = transactions_col()
logs_collection = logs_col()
audit_logs_collection = audit_logs_col()
invites_collection = invites_col()
password_resets_collection = password_resets_col()
facilities_collection = facilities_col()
menu_collection = menu_col()
housekeeping_tasks_collection = housekeeping_tasks_col()
maintenance_tickets_collection = maintenance_tickets_col()
laundry_tasks_collection = laundry_tasks_col()
room_service_orders_collection = orders_col()
security_incidents_collection = security_incidents_col()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') != 'production')
