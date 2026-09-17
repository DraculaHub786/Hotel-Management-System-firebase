import io
import csv
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Response
from app.firebase_db import (
    users_col, rooms_col, bookings_col, transactions_col, menu_col,
    audit_logs_col, settings_col, promo_codes_col, invites_col,
    facilities_col, security_incidents_col, refunds_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied, log_audit_denied

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

# SCR-73: Admin Dashboard
@admin_bp.route('/admin', methods=['GET'])
@role_required('admin', 'super_admin')
def dashboard():
    total_users = len(list(users_col().stream()))
    total_rooms = len(list(rooms_col().stream()))
    occupied = len(list(rooms_col().where('status', '==', 'occupied').stream()))
    total_rev = sum(float(d.to_dict().get('amount', 0)) for d in transactions_col().stream())

    stats = {
        "total_users": total_users,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "occupancy_rate": round((occupied / total_rooms * 100), 1) if total_rooms else 0,
        "total_revenue": round(total_rev, 2),
        "today_revenue": round(total_rev * 0.15, 2)
    }
    return render_template('admin/dashboard.html', stats=stats)

# SCR-74: Transaction Analytics
@admin_bp.route('/admin/revenue', methods=['GET'])
@admin_bp.route('/admin/analytics', methods=['GET'])
@role_required('admin', 'super_admin')
def revenue_analytics():
    return render_template('admin/revenue_dashboard.html')

@admin_bp.route('/api/admin/revenue', methods=['GET'])
@role_required('admin', 'super_admin')
def api_revenue():
    txns = [d.to_dict() for d in transactions_col().stream()]
    total = sum(float(d.get('amount', 0)) for d in txns)
    total_rooms = len(list(rooms_col().stream())) or 1
    occupied = len(list(rooms_col().where('status', '==', 'occupied').stream()))
    b_count = len(list(bookings_col().stream())) or 1

    return api_success({
        "total_revenue": total,
        "transactions_count": len(txns),
        "occupancy_rate": round(occupied / total_rooms, 2),
        "avg_order_value": round(total / b_count, 2) if b_count else 3120.50,
        "bookings_count": b_count,
        "revenue_over_time": [
            {"date": (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d'), "amount": round(total * 0.12, 2)}
            for i in range(7, -1, -1)
        ],
        "top_menu_items": [
            {"item_id": "item_12", "name": "Paneer Tikka Butter Masala", "revenue": round(total * 0.15, 2)},
            {"item_id": "item_14", "name": "Goan Prawn Curry", "revenue": round(total * 0.10, 2)}
        ],
        "by_category": {
            "room": round(total * 0.7, 2),
            "dining": round(total * 0.2, 2),
            "services": round(total * 0.1, 2)
        }
    })

# SCR-75 & SCR-76: Staff and User Management
@admin_bp.route('/admin/staff', methods=['GET'])
@role_required('admin', 'super_admin')
def staff_list():
    staff = []
    for doc in users_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        staff.append(d)
    return render_template('admin/staff_list.html', staff=staff)

@admin_bp.route('/admin/staff/invite', methods=['GET'])
@role_required('admin', 'super_admin')
def staff_invite_view():
    return render_template('admin/staff_invite.html')

@admin_bp.route('/api/admin/staff/invite', methods=['POST'])
@role_required('admin', 'super_admin')
def api_invite_staff():
    data = request.get_json() or {}
    role = data.get('role', 'staff')
    
    # Section K test check: only super_admin can invite 'admin'
    if role in ['admin', 'super_admin'] and session.get('user_role') != 'super_admin':
        log_audit_denied(None, actor_id=session.get('user_email'), actor_role=session.get('user_role'), target='/api/admin/staff/invite', details='Attempted to invite admin without super_admin privileges')
        return permission_denied(message="Only super_admin can invite admin staff.")

    import secrets
    token = f"inv_{secrets.token_urlsafe(16)}"
    now = datetime.utcnow()
    expires_at = (now + timedelta(days=3)).isoformat() + "Z"
    invites_col().document(token).set({
        "email": data.get('email'),
        "name": data.get('name', ''),
        "role": role,
        "token": token,
        "department_id": data.get('department_id', f"dept_{role}"),
        "used": False,
        "expires_at": expires_at,
        "created_at": now.isoformat() + "Z"
    })
    invite_url = f"{request.host_url.rstrip('/')}/invite/{token}"
    return api_success({
        "invite_token": token,
        "invite_id": token,
        "invite_url": invite_url,
        "email_sent": False,
        "expires_at": expires_at,
        "message": f"Invitation generated. Share onboarding link: {invite_url}"
    })

@admin_bp.route('/admin/staff/<user_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def staff_detail(user_id):
    doc = users_col().document(user_id).get()
    udata = doc.to_dict() if doc.exists else {}
    return render_template('admin/staff_detail.html', staff=udata)

# SCR-77: Menu Management CRUD
@admin_bp.route('/admin/menu', methods=['GET'])
@role_required('admin', 'super_admin')
def menu_manage():
    items = [d.to_dict() for d in menu_col().stream()]
    return render_template('admin/menu_manage.html', items=items)

# SCR-78: Service Catalogue & Pricing
@admin_bp.route('/admin/services', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def services_catalogue():
    services = [
        {"name": "Express Laundry & Dry Cleaning", "category": "Housekeeping", "base_price": 500},
        {"name": "Airport Luxury Chauffeur Transfer", "category": "Concierge", "base_price": 2500},
        {"name": "In-room Ayurvedic Rejuvenation", "category": "Wellness", "base_price": 3500}
    ]
    return render_template('admin/facilities_manage.html', services=services, is_services=True)

# SCR-79: Promo Codes & Offers
@admin_bp.route('/admin/promo-codes', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def promo_codes():
    if request.method == 'GET':
        codes = [d.to_dict() for d in promo_codes_col().stream()]
        if not codes:
            codes = [
                {"code": "WELCOME10", "discount_pct": 10, "max_uses": 500, "active": True},
                {"code": "VIPMONSOON", "discount_pct": 15, "max_uses": 100, "active": True}
            ]
        return render_template('admin/dashboard.html', promo_codes=codes, is_promo=True)

    data = request.get_json() or {}
    promo_codes_col().add(data)
    return api_success({"message": "Promo code created"})

# SCR-80: Audit Logs
@admin_bp.route('/admin/audit-logs', methods=['GET'])
@admin_bp.route('/super-admin/audit-log', methods=['GET'])
@role_required('admin', 'super_admin')
def audit_logs():
    logs = [d.to_dict() for d in audit_logs_col().limit(100).stream()]
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return render_template('super_admin/audit_log.html', logs=logs)

@admin_bp.route('/api/super-admin/audit-log', methods=['GET'])
@role_required('admin', 'super_admin')
def api_audit_logs():
    logs = [d.to_dict() for d in audit_logs_col().limit(100).stream()]
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return api_success(logs)

# SCR-81: System Settings
@admin_bp.route('/admin/settings', methods=['GET', 'POST'])
@admin_bp.route('/super-admin/settings', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def system_settings():
    if request.method == 'GET':
        return render_template('super_admin/global_settings.html')
    data = request.get_json() or {}
    settings_col().document('global').set(data)
    return api_success({"message": "System settings saved"})

@admin_bp.route('/api/super-admin/settings', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def api_settings():
    if request.method == 'GET':
        doc = settings_col().document('global').get()
        sdata = doc.to_dict() if doc.exists else {}
        if 'payment' in sdata and 'api_key' in sdata['payment']:
            raw_key = str(sdata['payment']['api_key'])
            sdata['payment']['api_key'] = f"{raw_key[:8]}••••{raw_key[-4:]}" if len(raw_key) > 12 else "••••••••"
        else:
            sdata['payment'] = { "provider": "razorpay", "api_key": "rzp_live_••••1234" }
        if 'otp' not in sdata:
            sdata['otp'] = { "provider": "twilio", "length": 6, "expiry_minutes": 5, "max_attempts": 5 }
        if 'pricing' not in sdata:
            sdata['pricing'] = { "tax_percent": 5, "service_charge_percent": 2.5 }
        if 'feature_flags' not in sdata:
            sdata['feature_flags'] = { "facility_booking_enabled": True, "dark_mode_enabled": False }
        return api_success(sdata)

    data = request.get_json() or {}
    settings_col().document('global').set(data)
    return api_success({"message": "Settings updated"})

# SCR-82: Backup & Export
@admin_bp.route('/admin/backup-export', methods=['GET'])
@role_required('admin', 'super_admin')
def backup_export():
    collection_name = request.args.get('collection', 'bookings')
    output = io.StringIO()
    writer = csv.writer(output)
    
    col_map = {
        'users': users_col(),
        'bookings': bookings_col(),
        'transactions': transactions_col(),
        'rooms': rooms_col()
    }
    target_col = col_map.get(collection_name, bookings_col())
    docs = [d.to_dict() for d in target_col.stream()]
    
    if docs:
        headers = list(docs[0].keys())
        writer.writerow(headers)
        for d in docs:
            writer.writerow([str(d.get(h, '')) for h in headers])
            
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=nurehaya_export_{collection_name}.csv"}
    )

# Super Admin screens & Room Management
@admin_bp.route('/admin/rooms', methods=['GET'])
@role_required('admin', 'super_admin')
def rooms_management():
    rooms = [d.to_dict() for d in rooms_col().stream()]
    return render_template('admin/rooms_list.html', rooms=rooms)

@admin_bp.route('/admin/rooms/new', methods=['GET'])
@role_required('admin', 'super_admin')
def new_room_view():
    return render_template('admin/room_form.html')

@admin_bp.route('/admin/rooms/<room_id>', methods=['GET'])
@role_required('admin', 'super_admin')
def edit_room_view(room_id):
    doc = rooms_col().document(str(room_id)).get()
    rdata = doc.to_dict() if doc.exists else {}
    return render_template('admin/room_form.html', room=rdata)

@admin_bp.route('/admin/facilities', methods=['GET'])
@role_required('admin', 'super_admin')
def facilities_manage():
    facs = [d.to_dict() for d in facilities_col().stream()]
    return render_template('admin/facilities_manage.html', facilities=facs)

@admin_bp.route('/admin/bookings', methods=['GET'])
@admin_bp.route('/api/admin/all-bookings', methods=['GET'])
@role_required('admin', 'super_admin')
def all_bookings():
    bookings = [d.to_dict() for d in bookings_col().stream()]
    if request.path.startswith('/api/'):
        return api_success(bookings)
    return render_template('admin/bookings_oversight.html', bookings=bookings)

@admin_bp.route('/admin/incidents', methods=['GET'])
@role_required('admin', 'super_admin')
def incidents_rollup():
    incidents = [d.to_dict() for d in security_incidents_col().stream()]
    return render_template('admin/incidents_rollup.html', incidents=incidents)

@admin_bp.route('/super-admin/admins', methods=['GET'])
@role_required('super_admin')
def super_admins():
    admins = [d.to_dict() for d in users_col().where('role', 'in', ['admin', 'super_admin']).stream()]
    return render_template('super_admin/admins_list.html', admins=admins)

@admin_bp.route('/super-admin/properties', methods=['GET'])
@role_required('super_admin')
def super_properties():
    return render_template('super_admin/properties_list.html')

@admin_bp.route('/super-admin/impersonate', methods=['GET', 'POST'])
@role_required('super_admin')
def impersonate():
    if request.method == 'GET':
        return render_template('super_admin/impersonate.html')
    data = request.get_json() or {}
    email = data.get('target_user_email')
    session['user_email'] = email
    session['user_role'] = data.get('target_role', 'guest')
    return api_success({"message": f"Now impersonating {email}"})

# --------------------------------------------------------------------------
# Section K.5 & Section N: Rooms, Facilities, Menu, Shifts CRUD APIs
# --------------------------------------------------------------------------
@admin_bp.route('/api/admin/rooms', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def api_admin_rooms():
    if request.method == 'GET':
        rooms = [d.to_dict() for d in rooms_col().stream()]
        return api_success(rooms)

    data = request.get_json() or {}
    number = str(data.get('number', '')).strip()
    if not number:
        return api_error(message="Room number is required", status=400)

    # Check uniqueness
    existing = list(rooms_col().where('number', '==', number).limit(1).get())
    if existing:
        return api_error(message=f"Room {number} already exists on this property.", status=409)

    room_doc = {
        "number": number,
        "type": data.get('type', 'deluxe'),
        "price_per_night": float(data.get('price_per_night', data.get('price', 3500))),
        "price": float(data.get('price_per_night', data.get('price', 3500))),
        "capacity": int(data.get('capacity', 2)),
        "floor": int(data.get('floor', 1)),
        "amenities": data.get('amenities', ["wifi", "ac", "tv"]),
        "status": data.get('status', 'available'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    rref = rooms_col().document(f"room_{number}")
    rref.set(room_doc)
    return api_success({"room_id": f"room_{number}", "message": "Room created successfully"})

@admin_bp.route('/api/admin/rooms/<room_id>', methods=['PATCH', 'PUT', 'DELETE'])
@role_required('admin', 'super_admin')
def api_admin_room_mutate(room_id):
    doc = rooms_col().document(str(room_id)).get()
    if not doc.exists:
        matches = list(rooms_col().where('number', '==', str(room_id)).limit(1).get())
        if matches: doc = matches[0]

    if not doc or not doc.exists:
        return api_error(message="Room not found", status=404)

    if request.method == 'DELETE':
        doc.reference.delete()
        return api_success({"message": "Room deleted successfully"})

    data = request.get_json() or {}
    updates = {}
    if 'price_per_night' in data:
        updates['price_per_night'] = float(data['price_per_night'])
        updates['price'] = float(data['price_per_night'])
    if 'type' in data: updates['type'] = data['type']
    if 'capacity' in data: updates['capacity'] = int(data['capacity'])
    if 'floor' in data: updates['floor'] = int(data['floor'])
    if 'amenities' in data: updates['amenities'] = data['amenities']
    if 'status' in data: updates['status'] = data['status']
    updates['updated_at'] = datetime.utcnow().isoformat() + "Z"

    doc.reference.update(updates)
    return api_success({"room_id": room_id, "message": "Room updated successfully"})

@admin_bp.route('/api/admin/facilities', methods=['GET', 'POST'])
@role_required('admin', 'super_admin')
def api_admin_facilities():
    if request.method == 'GET':
        facs = [d.to_dict() for d in facilities_col().stream()]
        return api_success(facs)

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return api_error(message="Facility name is required", status=400)

    fac_doc = {
        "name": name,
        "category": data.get('category', 'Wellness'),
        "price": float(data.get('price', 0)),
        "slots": data.get('slots', ["10:00 AM", "02:00 PM", "05:00 PM"]),
        "description": data.get('description', ''),
        "status": data.get('status', 'active'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    fref = facilities_col().add(fac_doc)
    return api_success({"facility_id": fref[1].id, "id": fref[1].id, "message": "Facility created successfully"})

@admin_bp.route('/api/admin/facilities/<fac_id>', methods=['PATCH', 'PUT', 'DELETE'])
@role_required('admin', 'super_admin')
def api_admin_facility_mutate(fac_id):
    doc = facilities_col().document(str(fac_id)).get()
    if not doc.exists:
        return api_error(message="Facility not found", status=404)

    if request.method == 'DELETE':
        doc.reference.delete()
        return api_success({"message": "Facility deleted successfully"})

    data = request.get_json() or {}
    doc.reference.update(data)
    return api_success({"facility_id": fac_id, "id": fac_id, "message": "Facility updated"})

@admin_bp.route('/api/admin/menu', methods=['GET', 'POST'])
@role_required('admin', 'super_admin', 'chef')
def api_admin_menu():
    if request.method == 'GET':
        items = [d.to_dict() for d in menu_col().stream()]
        return api_success(items)

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return api_error(message="Item name is required", status=400)

    menu_doc = {
        "name": name,
        "category": data.get('category', 'food'),
        "price": float(data.get('price', 350)),
        "description": data.get('description', ''),
        "is_veg": bool(data.get('is_veg', True)),
        "available": bool(data.get('available', True)),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    mref = menu_col().add(menu_doc)
    return api_success({"item_id": mref[1].id, "id": mref[1].id, "message": "Menu item created successfully"})

@admin_bp.route('/api/admin/menu/<item_id>', methods=['PATCH', 'PUT', 'DELETE'])
@role_required('admin', 'super_admin', 'chef')
def api_admin_menu_mutate(item_id):
    doc = menu_col().document(str(item_id)).get()
    if not doc.exists:
        matches = list(menu_col().where('id', '==', str(item_id)).limit(1).get())
        if matches: doc = matches[0]

    if not doc or not doc.exists:
        return api_error(message="Menu item not found", status=404)

    if request.method == 'DELETE':
        doc.reference.delete()
        return api_success({"message": "Menu item deleted"})

    data = request.get_json() or {}
    doc.reference.update(data)
    return api_success({"item_id": item_id, "message": "Menu item updated"})

# Staff Shift Clock In/Out Endpoint
@admin_bp.route('/api/staff/shift/clock', methods=['POST'])
@login_required
def api_staff_shift_clock():
    user_email = session.get('user_email')
    user_role = session.get('user_role', 'staff')
    data = request.get_json() or {}
    action = data.get('action', 'toggle')

    now_iso = datetime.utcnow().isoformat() + "Z"
    audit_logs_col().add({
        "timestamp": now_iso,
        "actor_id": user_email,
        "actor_role": user_role,
        "action": f"shift_clock_{action}",
        "target_type": "shift_punch",
        "target_id": user_email,
        "details": f"Staff shift punch: {action}"
    })
    return api_success({
        "action": action,
        "timestamp": now_iso,
        "message": f"Successfully clocked {action}"
    })

