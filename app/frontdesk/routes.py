import time
import random
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    rooms_col, bookings_col, users_col, transactions_col,
    housekeeping_tasks_col, night_audits_col, audit_logs_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from guest_service import generate_qr_base64

logger = logging.getLogger(__name__)

frontdesk_bp = Blueprint('frontdesk', __name__)

def generate_booking_no():
    return f"BK{int(time.time())}{random.randint(100, 999)}"

# Guest Screens (C.1 - C.9) & Front Office
@frontdesk_bp.route('/rooms', methods=['GET'])
def rooms_catalog():
    # Fetch rooms
    rooms = []
    for doc in rooms_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        rooms.append(d)
    return render_template('guest/rooms.html', rooms=rooms)

@frontdesk_bp.route('/rooms/<room_id>', methods=['GET'])
def room_detail(room_id):
    doc = rooms_col().document(str(room_id)).get()
    if not doc.exists:
        matches = list(rooms_col().where('number', '==', str(room_id)).limit(1).get())
        if matches:
            doc = matches[0]
    if not doc or not doc.exists:
        return render_template('permission_denied.html', message="Room not found", user_role="guest"), 404
    rdata = doc.to_dict()
    rdata['id'] = doc.id
    return render_template('guest/room_detail.html', room=rdata)

@frontdesk_bp.route('/api/rooms', methods=['GET', 'POST'])
def api_rooms_list():
    if request.method == 'GET':
        rooms = []
        for doc in rooms_col().stream():
            d = doc.to_dict()
            d['id'] = doc.id
            rooms.append(d)
        return api_success(rooms)

    # Admin room creation
    if session.get('user_role') not in ['admin', 'manager']:
        return permission_denied()
    data = request.get_json() or {}
    new_doc = rooms_col().add(data)
    return api_success({"id": new_doc[1].id, "message": "Room created successfully"})

@frontdesk_bp.route('/api/rooms/available', methods=['GET'])
def api_rooms_available():
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    room_type = request.args.get('type')

    all_rooms = []
    for doc in rooms_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        if d.get('status') != 'blocked':
            all_rooms.append(d)

    if room_type:
        all_rooms = [r for r in all_rooms if r.get('type', '').lower() == room_type.lower()]

    def _respond(data):
        if request.args.get('format') == 'envelope':
            return api_success(data)
        return jsonify(data)

    if not check_in or not check_out:
        return _respond(all_rooms)

    def _parse_dt(val):
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        if hasattr(val, 'to_datetime'):
            return val.to_datetime()
        s = str(val).strip().replace('Z', '')
        for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(s.split('.')[0] if fmt == '%Y-%m-%dT%H:%M:%S' else s, fmt)
            except Exception:
                pass
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None

    # Date overlap check with active bookings
    ci_req = _parse_dt(check_in)
    co_req = _parse_dt(check_out)
    if not ci_req or not co_req:
        return _respond(all_rooms)

    booked_room_ids = set()
    for bdoc in bookings_col().stream():
        b = bdoc.to_dict()
        if b.get('status') in ['confirmed', 'checked_in']:
            b_ci = _parse_dt(b.get('check_in'))
            b_co = _parse_dt(b.get('check_out'))
            if b_ci and b_co:
                # Overlap condition: max(ci_req, b_ci) < min(co_req, b_co)
                if max(ci_req, b_ci) < min(co_req, b_co):
                    if b.get('room_id'):
                        booked_room_ids.add(str(b.get('room_id')))
                    if b.get('room_number'):
                        booked_room_ids.add(str(b.get('room_number')))

    avail = [r for r in all_rooms if str(r['id']) not in booked_room_ids and str(r.get('number')) not in booked_room_ids]
    return _respond(avail)

@frontdesk_bp.route('/checkout', methods=['GET'])
@login_required
def checkout_view():
    return render_template('guest/checkout.html')

@frontdesk_bp.route('/api/cart/checkout', methods=['POST'])
@login_required
def cart_checkout_api():
    user_email = session.get('user_email')
    user_role = session.get('user_role', 'guest')
    body = request.get_json() or {}
    items = body.get('items', [])
    payment_method = body.get('payment_method', 'card')

    if not items:
        return api_error(message="Cart is empty", status=400)

    # Recalculate prices from Firestore
    subtotal = 0.0
    detailed_items = []
    is_member = (user_role == 'member')

    for itm in items:
        price = 3500.0
        name = "Deluxe Room"
        ref_id = itm.get('ref_id', '101')
        doc = rooms_col().document(str(ref_id)).get()
        if not doc.exists:
            matches = list(rooms_col().where('number', '==', str(ref_id)).limit(1).get())
            if matches: doc = matches[0]
        if doc and doc.exists:
            price = float(doc.to_dict().get('price', 3500))
            name = f"Room {doc.to_dict().get('number', ref_id)}"
            
        nights = 1
        if itm.get('check_in') and itm.get('check_out'):
            try:
                ci = datetime.fromisoformat(itm['check_in'].replace('Z', ''))
                co = datetime.fromisoformat(itm['check_out'].replace('Z', ''))
                nights = max(1, (co - ci).days)
            except Exception:
                nights = 1

        line_total = price * nights
        subtotal += line_total
        detailed_items.append({
            "name": name,
            "room_id": ref_id,
            "room_number": itm.get('room_number', str(ref_id)),
            "check_in": itm.get('check_in'),
            "check_out": itm.get('check_out'),
            "price": price,
            "nights": nights,
            "total": line_total
        })

    # Member 5% discount
    discount_pct = 5.0 if is_member else 0.0
    discount_amt = round(subtotal * (discount_pct / 100.0), 2)
    tax_amt = round((subtotal - discount_amt) * 0.05, 2)
    total_amt = round(subtotal - discount_amt + tax_amt, 2)

    booking_no = generate_booking_no()
    primary_item = detailed_items[0] if detailed_items else {}

    booking_doc = {
        "booking_no": booking_no,
        "user_email": user_email,
        "guest_name": body.get('billing_info', {}).get('name') or session.get('user_name', user_email),
        "room_id": primary_item.get('room_id'),
        "room_number": primary_item.get('room_number'),
        "check_in": primary_item.get('check_in'),
        "check_out": primary_item.get('check_out'),
        "guests": int(body.get('guests', 1)),
        "subtotal": subtotal,
        "discount_percent": discount_pct,
        "discount_amount": discount_amt,
        "tax": tax_amt,
        "total_price": total_amt,
        "status": "confirmed",
        "source": "web",
        "payment_method": payment_method,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    bref = bookings_col().add(booking_doc)
    booking_id = bref[1].id

    # Create transaction
    txn_id = f"TXN{int(time.time())}{random.randint(1000, 9999)}"
    transactions_col().add({
        "transaction_id": txn_id,
        "user_email": user_email,
        "amount": total_amt,
        "payment_method": payment_method,
        "payment_status": "completed",
        "category": "room",
        "booking_id": booking_id,
        "reference_no": booking_no,
        "created_at": datetime.utcnow().isoformat() + "Z"
    })

    return api_success({
        "booking_id": booking_id,
        "booking_no": booking_no,
        "total": total_amt,
        "redirect_url": f"/confirmation/{booking_id}"
    })

@frontdesk_bp.route('/confirmation/<booking_id>', methods=['GET'])
@login_required
def confirmation_view(booking_id):
    bdoc = bookings_col().document(booking_id).get()
    bdata = bdoc.to_dict() if bdoc.exists else {}
    if not bdata:
        # Check by booking_no
        matches = list(bookings_col().where('booking_no', '==', booking_id).limit(1).get())
        if matches: bdata = matches[0].to_dict()
    
    # Generate QR ticket
    qr_payload = f"NUR-E-HAYA:TICKET:{bdata.get('booking_no')}:{bdata.get('room_number')}:{bdata.get('check_in')}"
    qr_code = generate_qr_base64(qr_payload)

    return render_template('guest/confirmation.html', booking=bdata, qr_code=qr_code, booking_id=booking_id)

@frontdesk_bp.route('/my-bookings', methods=['GET'])
@login_required
def my_bookings_view():
    email = session.get('user_email')
    user_bookings = []
    for doc in bookings_col().where('user_email', '==', email).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        user_bookings.append(d)
    user_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('guest/my_bookings.html', bookings=user_bookings)

@frontdesk_bp.route('/api/user/bookings', methods=['GET'])
@login_required
def api_user_bookings():
    email = session.get('user_email')
    user_bookings = []
    for doc in bookings_col().where('user_email', '==', email).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        user_bookings.append(d)
    return api_success(user_bookings)

@frontdesk_bp.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
@login_required
def api_cancel_booking(booking_id):
    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)
    bdata = bdoc.to_dict()
    if session.get('user_role') not in ['admin', 'manager', 'front_desk'] and bdata.get('user_email') != session.get('user_email'):
        return permission_denied()

    bdoc.reference.update({"status": "cancelled"})
    return api_success({"message": "Booking cancelled successfully"})

# Front Desk Operations (SCR-18 to SCR-23)
@frontdesk_bp.route('/frontdesk/checkin', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def checkin_view():
    arrivals = [d.to_dict() for d in bookings_col().stream()]
    return render_template('frontdesk/checkin.html', arrivals=arrivals)

@frontdesk_bp.route('/frontdesk/checkout', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def checkout_view_desk():
    in_house = [d.to_dict() for d in bookings_col().where('status', '==', 'checked_in').stream()]
    return render_template('frontdesk/checkout_settle.html', in_house_bookings=in_house)

@frontdesk_bp.route('/frontdesk/guests', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def guest_history():
    guests = [d.to_dict() for d in users_col().where('role', 'in', ['guest', 'user', 'member']).stream()]
    return render_template('frontdesk/guest_history.html', guests=guests)

@frontdesk_bp.route('/staff/front-desk', methods=['GET'])
@frontdesk_bp.route('/frontdesk', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def frontdesk_dashboard():
    # Arrivals, departures, occupancy
    today_str = datetime.utcnow().date().isoformat()
    arrivals = []
    departures = []
    for doc in bookings_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        if d.get('check_in', '').startswith(today_str):
            arrivals.append(d)
        if d.get('check_out', '').startswith(today_str):
            departures.append(d)

    return render_template('frontdesk/arrivals_departures.html', arrivals=arrivals, departures=departures)

@frontdesk_bp.route('/staff/front-desk/rooms', methods=['GET'])
@frontdesk_bp.route('/frontdesk/rooms', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def room_board():
    rooms = []
    for doc in rooms_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        rooms.append(d)
    rooms.sort(key=lambda x: str(x.get('number', '0')))
    return render_template('frontdesk/room_status_board.html', rooms=rooms)

@frontdesk_bp.route('/api/front-desk/room-board', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def api_room_board():
    rooms = []
    for doc in rooms_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        rooms.append(d)
    return api_success(rooms)

@frontdesk_bp.route('/api/front-desk/checkin', methods=['POST'])
@role_required('admin', 'manager', 'front_desk')
def api_frontdesk_checkin():
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    room_number = data.get('room_number')

    if not booking_id:
        return api_error(message="booking_id is required", status=400)

    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)

    bdoc.reference.update({"status": "checked_in", "checked_in_at": datetime.utcnow().isoformat() + "Z"})
    
    # Mark room as occupied
    rnum = room_number or bdoc.to_dict().get('room_number')
    if rnum:
        for rdoc in rooms_col().where('number', '==', str(rnum)).stream():
            rdoc.reference.update({"status": "occupied"})

    return api_success({"message": "Guest checked in successfully"})

@frontdesk_bp.route('/api/front-desk/checkout', methods=['POST'])
@role_required('admin', 'manager', 'front_desk')
def api_frontdesk_checkout():
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    
    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)

    bdata = bdoc.to_dict()
    bdoc.reference.update({"status": "checked_out", "checked_out_at": datetime.utcnow().isoformat() + "Z"})

    # Mark room as cleaning & trigger housekeeping task!
    rnum = bdata.get('room_number')
    if rnum:
        for rdoc in rooms_col().where('number', '==', str(rnum)).stream():
            rdoc.reference.update({"status": "cleaning"})
            
        # Create housekeeping task
        housekeeping_tasks_col().add({
            "task_no": f"TSK{int(time.time())}",
            "room_number": str(rnum),
            "type": "checkout_cleaning",
            "priority": "high",
            "status": "pending",
            "description": f"Turnover cleaning after checkout for Room {rnum}",
            "created_at": datetime.utcnow().isoformat() + "Z"
        })

    return api_success({"message": "Guest checked out. Room marked for cleaning."})

@frontdesk_bp.route('/api/front-desk/mark-clean', methods=['POST'])
@role_required('admin', 'manager', 'front_desk', 'housekeeping')
def api_mark_room_clean():
    data = request.get_json() or {}
    room_id = data.get('room_id')
    doc = rooms_col().document(str(room_id)).get()
    if doc.exists:
        doc.reference.update({"status": "available"})
        return api_success({"message": "Room status updated to available"})
    return api_error(message="Room not found", status=404)

@frontdesk_bp.route('/frontdesk/walkin', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'front_desk')
def walkin_registration():
    if request.method == 'GET':
        avail_rooms = [d.to_dict() for d in rooms_col().where('status', '==', 'available').stream()]
        return render_template('frontdesk/walkin.html', available_rooms=avail_rooms)

    data = request.get_json() or {}
    guest_name = data.get('guest_name')
    room_number = data.get('room_number')
    total_price = float(data.get('total_price', 3500))

    bno = generate_booking_no()
    bdoc = {
        "booking_no": bno,
        "guest_name": guest_name,
        "user_email": data.get('email', 'walkin@nur-e-haya.com'),
        "room_number": room_number,
        "check_in": datetime.utcnow().date().isoformat(),
        "check_out": (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
        "total_price": total_price,
        "status": "checked_in",
        "source": "walkin",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    bref = bookings_col().add(bdoc)

    for rdoc in rooms_col().where('number', '==', str(room_number)).stream():
        rdoc.reference.update({"status": "occupied"})

    return api_success({"booking_id": bref[1].id, "booking_no": bno, "message": "Walk-in registered and checked in."})

@frontdesk_bp.route('/frontdesk/night-audit', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'front_desk')
def night_audit():
    if request.method == 'GET':
        audits = [d.to_dict() for d in night_audits_col().stream()]
        audits.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return render_template('frontdesk/night_audit.html', audits=audits)

    # Perform EOD Night Audit calculation
    today_str = datetime.utcnow().date().isoformat()
    total_rooms = len(list(rooms_col().stream()))
    occupied = len(list(rooms_col().where('status', '==', 'occupied').stream()))
    occupancy_pct = round((occupied / total_rooms * 100), 1) if total_rooms else 0

    daily_rev = 0.0
    for tx in transactions_col().where('created_at', '>=', today_str).stream():
        daily_rev += float(tx.to_dict().get('amount', 0.0))

    audit_entry = {
        "audit_date": today_str,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "occupancy_rate": occupancy_pct,
        "total_revenue": daily_rev,
        "audited_by": session.get('user_email'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    night_audits_col().add(audit_entry)
    return api_success({"message": "Night audit completed successfully.", "audit": audit_entry})
