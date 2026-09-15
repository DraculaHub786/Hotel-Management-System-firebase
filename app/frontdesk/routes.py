import time
import random
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    get_db, rooms_col, bookings_col, users_col, transactions_col, orders_col,
    housekeeping_tasks_col, night_audits_col, audit_logs_col, service_requests_col,
    spa_bookings_col, pool_bookings_col, gym_bookings_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from guest_service import generate_qr_base64, calculate_order_pricing

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
        wing = request.args.get('wing')
        floor = request.args.get('floor')
        status = request.args.get('status')
        rooms = []
        for doc in rooms_col().stream():
            d = doc.to_dict()
            d['id'] = doc.id
            if wing and str(d.get('wing', '')).lower() != wing.lower():
                continue
            if floor and str(d.get('floor', '')).lower() != floor.lower():
                continue
            if status and str(d.get('status', '')).lower() != status.lower():
                continue
            rooms.append(d)
        return api_success(rooms)

    # Admin room creation
    if session.get('user_role') not in ['admin', 'manager']:
        return permission_denied()
    data = request.get_json() or {}
    new_doc = rooms_col().add(data)
    return api_success({"id": new_doc[1].id, "message": "Room created successfully"})

@frontdesk_bp.route('/api/guest/room-service/request', methods=['POST'])
@login_required
def api_guest_room_service_request():
    data = request.get_json() or {}
    service_type = data.get('service_type', 'cleaning')
    room_number = str(data.get('room_number', '')).strip()
    notes = data.get('notes', '') or data.get('description', '')
    user_email = session.get('user_email', '')
    now_iso = datetime.utcnow().isoformat() + "Z"

    # Auto-resolve room number from active booking if not specified
    if not room_number:
        for b in bookings_col().where('user_email', '==', user_email).where('status', '==', 'checked_in').stream():
            room_number = str(b.to_dict().get('room_number', ''))
            break
    if not room_number:
        room_number = "HW-101"

    req_id = f"REQ{int(time.time())}{random.randint(10, 99)}"

    # Helper for updating room status across various identifiers (RW-301, 301, room_301, rm_RW-301)
    def _apply_room_updates(fields):
        num_part = room_number.split('-')[-1]
        for rdoc in rooms_col().where('number', '==', room_number).stream():
            rdoc.reference.update(fields)
        for rdoc in rooms_col().where('number', '==', num_part).stream():
            rdoc.reference.update(fields)
        for rdoc in rooms_col().where('flat_code', '==', room_number).stream():
            rdoc.reference.update(fields)
        for rdoc in rooms_col().where('flat_no', '==', room_number).stream():
            rdoc.reference.update(fields)
        for doc_key in [f"rm_{room_number}", f"room_{room_number}", f"room_{num_part}", f"rm_{num_part}", room_number]:
            rd = rooms_col().document(doc_key).get()
            if rd.exists:
                rd.reference.update(fields)

    # Handle express checkout / leaving
    if service_type in ['checkout_leaving', 'leaving']:
        # 1. Update room status to cleaning
        _apply_room_updates({"status": "cleaning", "occupied": False, "last_cleaned": now_iso})

        # 2. Update active booking status to checked_out
        num_part = room_number.split('-')[-1]
        for bdoc in bookings_col().where('status', '==', 'checked_in').stream():
            bdata = bdoc.to_dict()
            if str(bdata.get('room_number')) in [room_number, num_part]:
                bdoc.reference.update({"status": "checked_out", "checked_out_at": now_iso})

        # 3. Create urgent turnover cleaning task for Housekeeping
        htask = housekeeping_tasks_col().add({
            "task_no": f"TSK{int(time.time())}",
            "room_number": room_number,
            "type": "checkout_clean",
            "priority": "urgent",
            "status": "pending",
            "description": f"Urgent Turnover Cleaning: Guest departure reported for Room {room_number}. Perform full deep sanitization and reset.",
            "created_from": "guest_express_checkout",
            "guest_notes": notes,
            "created_at": now_iso
        })
        return api_success({
            "request_id": req_id,
            "task_id": htask[1].id,
            "status": "checkout_processed",
            "message": f"Express checkout initiated for Room {room_number}. Housekeeping staff alerted for turnover cleaning."
        })

    # Handle Make Up Room (Cleaning)
    elif service_type in ['cleaning', 'make_up_room']:
        _apply_room_updates({"status": "cleaning", "service_needed": "cleaning"})

        htask = housekeeping_tasks_col().add({
            "task_no": f"TSK{int(time.time())}",
            "room_number": room_number,
            "type": "room_clean",
            "priority": "high",
            "status": "pending",
            "description": f"Guest requested 'Make Up Room' service for Room {room_number}. Notes: {notes}",
            "created_from": "guest_room_service_request",
            "created_at": now_iso
        })
        return api_success({
            "request_id": req_id,
            "task_id": htask[1].id,
            "status": "cleaning_dispatched",
            "message": f"Housekeeping team notified to make up Room {room_number}."
        })

    # Handle Do Not Disturb (DND)
    elif service_type == 'dnd':
        is_dnd = data.get('dnd', True)
        _apply_room_updates({"dnd": is_dnd})
        return api_success({
            "request_id": req_id,
            "dnd": is_dnd,
            "message": f"Do Not Disturb {'activated' if is_dnd else 'deactivated'} for Room {room_number}."
        })

    # General service request (laundry, concierge, amenities, etc.)
    else:
        sdoc = {
            "request_no": req_id,
            "user_email": user_email,
            "room_number": room_number,
            "service_type": service_type,
            "priority": data.get('priority', 'medium'),
            "description": notes,
            "status": "pending",
            "created_at": now_iso
        }
        sref = service_requests_col().add(sdoc)
        return api_success({
            "request_id": sref[1].id,
            "status": "pending",
            "message": f"Request for {service_type} received. Room service team dispatched."
        })


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

    is_member = (user_role == 'member')
    pricing = calculate_order_pricing(items, get_db(), is_member=is_member)

    booking_no = generate_booking_no()
    primary_room = next((it for it in pricing['items'] if it.get('type') == 'room'), None)
    if not primary_room and pricing['items']:
        primary_room = pricing['items'][0]

    now_iso = datetime.utcnow().isoformat() + "Z"
    txn_id = f"txn_{int(time.time())}_{random.randint(100, 999)}"

    booking_doc = {
        "booking_no": booking_no,
        "user_email": user_email,
        "guest_name": body.get('guest_name') or body.get('billing_info', {}).get('name') or session.get('user_name', user_email),
        "phone": body.get('phone', ''),
        "special_requests": body.get('special_requests', ''),
        "delivery_mode": body.get('delivery_mode', 'in_room'),
        "room_id": primary_room.get('ref_id') if primary_room else 'room_general',
        "room_number": primary_room.get('ref_id') if primary_room else '101',
        "check_in": primary_room.get('check_in', now_iso[:10]) if primary_room else now_iso[:10],
        "check_out": primary_room.get('check_out') if primary_room else (datetime.utcnow() + timedelta(days=1)).date().isoformat(),
        "guests": int(body.get('guests', 1)),
        "subtotal": pricing['subtotal'],
        "discount_amount": pricing['discount'],
        "tax": pricing['tax'],
        "service_charge": pricing['service_charge'],
        "total_price": pricing['total'],
        "items": pricing['items'],
        "status": "confirmed",
        "source": "web",
        "txn_id": txn_id,
        "payment_method": payment_method,
        "created_at": now_iso
    }

    bref = bookings_col().add(booking_doc)
    booking_id = bref[1].id

    # Create pending transaction with document ID matching txn_id and complete order_summary
    order_sum = {
        "subtotal": pricing['subtotal'],
        "discount": pricing['discount'],
        "tax": pricing['tax'],
        "service_charge": pricing['service_charge'],
        "total": pricing['total'],
        "currency": "INR"
    }
    dynamic_otp = f"{random.randint(100000, 999999)}"
    transactions_col().document(txn_id).set({
        "transaction_id": txn_id,
        "user_email": user_email,
        "amount": pricing['total'],
        "total": pricing['total'],
        "payment_method": payment_method,
        "payment_status": "pending",
        "status": "pending",
        "category": "multi",
        "booking_id": booking_id,
        "reference_no": booking_no,
        "order_summary": order_sum,
        "otp": dynamic_otp,
        "created_at": now_iso
    })

    checkout_banner = f"""
======================================================================
🔐 [NEW PAYMENT TRANSACTION INITIATED]
   Transaction ID : {txn_id}
   Booking Ref    : {booking_no}
   Amount Payable : ₹{pricing['total']}
   >>> 6-DIGIT OTP: {dynamic_otp} <<<
   Timestamp      : {now_iso}
   Instruction    : Enter the 6-digit OTP above on /pay/{txn_id}/otp
======================================================================
"""
    logger.info(checkout_banner)
    print(checkout_banner, flush=True)

    return api_success({
        "booking_id": booking_id,
        "booking_no": booking_no,
        "txn_id": txn_id,
        "order_summary": order_sum,
        "total": pricing['total'],
        "redirect_url": f"/pay/{txn_id}"
    })

@frontdesk_bp.route('/confirmation/<booking_id>', methods=['GET'])
@login_required
def confirmation_view(booking_id):
    bdoc = bookings_col().document(booking_id).get()
    bdata = bdoc.to_dict() if bdoc.exists else {}
    if not bdata:
        # Check by booking_no
        matches = list(bookings_col().where('booking_no', '==', booking_id).limit(1).get())
        if matches:
            bdata = matches[0].to_dict()

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

    user_orders = []
    for doc in orders_col().where('user_email', '==', email).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        user_orders.append(d)

    # Fetch spa & wellness facility bookings
    user_facilities = []
    for col_func in [spa_bookings_col, pool_bookings_col, gym_bookings_col]:
        try:
            for doc in col_func().where('user_email', '==', email).stream():
                d = doc.to_dict()
                d['id'] = doc.id
                user_facilities.append(d)
        except Exception as e:
            logger.warning(f"Error querying facility collection: {e}")

    user_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    user_facilities.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('guest/my_bookings.html', bookings=user_bookings, orders=user_orders, facilities=user_facilities)

@frontdesk_bp.route('/api/user/bookings', methods=['GET'])
@login_required
def api_user_bookings():
    email = session.get('user_email')
    user_bookings = []
    for doc in bookings_col().where('user_email', '==', email).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        user_bookings.append(d)
    user_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return api_success(user_bookings)

@frontdesk_bp.route('/api/user/orders', methods=['GET'])
@login_required
def api_user_orders():
    email = session.get('user_email')
    user_orders = []
    for doc in orders_col().where('user_email', '==', email).stream():
        d = doc.to_dict()
        d['id'] = doc.id
        user_orders.append(d)
    user_orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return api_success(user_orders)

@frontdesk_bp.route('/api/user/facilities', methods=['GET'])
@login_required
def api_user_facilities():
    email = session.get('user_email')
    user_facilities = []
    for col_func in [spa_bookings_col, pool_bookings_col, gym_bookings_col]:
        try:
            for doc in col_func().where('user_email', '==', email).stream():
                d = doc.to_dict()
                d['id'] = doc.id
                user_facilities.append(d)
        except Exception as e:
            logger.warning(f"Error querying facility collection: {e}")
    user_facilities.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return api_success(user_facilities)

@frontdesk_bp.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
@login_required
def api_cancel_booking(booking_id):
    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)
    bdata = bdoc.to_dict()

    user_role = session.get('user_role', 'guest')
    user_email = session.get('user_email', '')

    if user_role not in ['admin', 'manager', 'front_desk'] and bdata.get('user_email') != user_email:
        return permission_denied()

    # Section C.9: cancellation only allowed if confirmed and > 24h prior to check-in
    if user_role not in ['admin', 'manager', 'front_desk']:
        if bdata.get('status') != 'confirmed':
            return api_error(message="Only confirmed bookings can be cancelled.", status=400)
        check_in_str = bdata.get('check_in')
        if check_in_str:
            try:
                ci_date = datetime.fromisoformat(check_in_str.replace('Z', '').split('T')[0])
                if (ci_date - datetime.utcnow().date()).total_days() < 1:
                    return api_error(message="Bookings can only be cancelled at least 24 hours prior to check-in date.", status=400)
            except Exception:
                pass

    bdoc.reference.update({"status": "cancelled", "cancelled_at": datetime.utcnow().isoformat() + "Z"})
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

@frontdesk_bp.route('/frontdesk/tape-chart', methods=['GET'])
@frontdesk_bp.route('/staff/front-desk/tape-chart', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def tape_chart_view():
    return render_template('frontdesk/tape_chart.html')

@frontdesk_bp.route('/api/front-desk/tape-chart', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def api_tape_chart():
    start_date_str = request.args.get('start_date')
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str).date()
        except Exception:
            start_date = datetime.utcnow().date()
    else:
        start_date = datetime.utcnow().date()

    # Generate 14-day window
    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(14)]

    rooms = []
    for doc in rooms_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        rooms.append(d)
    rooms.sort(key=lambda x: str(x.get('number', '0')))

    # Fetch overlapping bookings
    min_date = dates[0]
    max_date = dates[-1]
    bookings = []
    for bdoc in bookings_col().stream():
        bd = bdoc.to_dict()
        bd['id'] = bdoc.id
        cin = (bd.get('check_in') or '')[:10]
        cout = (bd.get('check_out') or '')[:10]
        if cin and cout and not (cout < min_date or cin > max_date):
            bookings.append(bd)

    return api_success({
        "dates": dates,
        "rooms": rooms,
        "bookings": bookings
    })

@frontdesk_bp.route('/api/front-desk/rooms/<room_id>/drawer', methods=['GET'])
@role_required('admin', 'manager', 'front_desk', 'housekeeping')
def api_room_drawer(room_id):
    doc = rooms_col().document(str(room_id)).get()
    if not doc.exists:
        matches = list(rooms_col().where('number', '==', str(room_id)).limit(1).get())
        if matches: doc = matches[0]

    if not doc or not doc.exists:
        return api_error(message="Room not found", status=404)

    rdata = doc.to_dict()
    rdata['id'] = doc.id
    rnum = str(rdata.get('number', ''))

    active_booking = None
    for b in bookings_col().where('room_number', '==', rnum).where('status', 'in', ['checked_in', 'confirmed']).stream():
        bdict = b.to_dict()
        bdict['id'] = b.id
        active_booking = bdict
        break

    active_hsk = None
    for h in housekeeping_tasks_col().where('room_number', '==', rnum).where('status', 'in', ['pending', 'in_progress']).stream():
        hdict = h.to_dict()
        hdict['id'] = h.id
        active_hsk = hdict
        break

    return api_success({
        "room": rdata,
        "active_booking": active_booking,
        "active_housekeeping": active_hsk
    })

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
    notes = data.get('notes', '')

    if not booking_id:
        return api_error(message="booking_id is required", status=400)

    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)

    now_iso = datetime.utcnow().isoformat() + "Z"
    bdoc.reference.update({
        "status": "checked_in",
        "checked_in_at": now_iso,
        "checkin_notes": notes
    })
    
    # Mark room as occupied
    rnum = room_number or bdoc.to_dict().get('room_number')
    if rnum:
        for rdoc in rooms_col().where('number', '==', str(rnum)).stream():
            rdoc.reference.update({"status": "occupied"})

    return api_success({
        "booking_id": booking_id,
        "status": "checked_in",
        "checked_in_at": now_iso,
        "message": "Guest checked in successfully"
    })

@frontdesk_bp.route('/api/front-desk/checkout', methods=['POST'])
@role_required('admin', 'manager', 'front_desk')
def api_frontdesk_checkout():
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    
    bdoc = bookings_col().document(booking_id).get()
    if not bdoc.exists:
        return api_error(message="Booking not found", status=404)

    bdata = bdoc.to_dict()
    now_iso = datetime.utcnow().isoformat() + "Z"
    bdoc.reference.update({
        "status": "checked_out",
        "checked_out_at": now_iso
    })

    # Mark room as cleaning & trigger housekeeping task (Section D.5 Automation)
    rnum = bdata.get('room_number')
    task_id = None
    if rnum:
        for rdoc in rooms_col().where('number', '==', str(rnum)).stream():
            rdoc.reference.update({"status": "cleaning"})
            
        htask = housekeeping_tasks_col().add({
            "task_no": f"TSK{int(time.time())}",
            "room_number": str(rnum),
            "type": "checkout_clean",
            "priority": "high",
            "status": "pending",
            "description": f"Turnover cleaning after checkout for Room {rnum}",
            "created_from": "booking_checkout",
            "created_at": now_iso
        })
        task_id = htask[1].id

    return api_success({
        "booking_id": booking_id,
        "status": "checked_out",
        "checked_out_at": now_iso,
        "housekeeping_task_id": task_id,
        "message": "Guest checked out. Housekeeping turnover task created."
    })

@frontdesk_bp.route('/api/front-desk/mark-clean', methods=['POST'])
@role_required('admin', 'manager', 'front_desk', 'housekeeping')
def api_mark_room_clean():
    data = request.get_json() or {}
    room_id = data.get('room_id') or data.get('room_number')
    if not room_id:
        return api_error(message="room_id or room_number is required", status=400)

    doc = rooms_col().document(str(room_id)).get()
    if not doc.exists:
        for field in ['number', 'flat_code', 'flat_no']:
            matches = list(rooms_col().where(field, '==', str(room_id)).limit(1).get())
            if matches:
                doc = matches[0]
                break

    if doc and doc.exists:
        doc.reference.update({"status": "available"})
        return api_success({"message": "Room status updated to available", "room_id": doc.id})
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

    # Perform Automated EOD Night Audit calculation
    today_str = datetime.utcnow().date().isoformat()
    total_rooms = len(list(rooms_col().stream()))
    occupied = len(list(rooms_col().where('status', '==', 'occupied').stream()))
    occupancy_pct = round((occupied / total_rooms * 100), 1) if total_rooms else 0.0

    daily_rev = 0.0
    for tx in transactions_col().where('created_at', '>=', today_str).stream():
        daily_rev += float(tx.to_dict().get('amount', 0.0))

    adr = round(daily_rev / occupied, 2) if occupied > 0 else 0.0
    revpar = round(daily_rev / total_rooms, 2) if total_rooms > 0 else 0.0

    # Check for no-shows
    no_shows_count = 0
    for b in bookings_col().where('status', '==', 'confirmed').stream():
        bd = b.to_dict()
        check_in_val = bd.get('check_in') or ''
        if check_in_val and check_in_val < today_str:
            b.reference.update({"status": "no_show", "marked_no_show_at": datetime.utcnow().isoformat() + "Z"})
            no_shows_count += 1

    audit_entry = {
        "audit_date": today_str,
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "occupancy_rate": occupancy_pct,
        "total_revenue": daily_rev,
        "average_daily_rate": adr,
        "revpar": revpar,
        "no_shows_processed": no_shows_count,
        "audited_by": session.get('user_email'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    night_audits_col().add(audit_entry)

    # Write audit log
    audit_logs_col().add({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "actor_id": session.get('user_email', 'system'),
        "actor_role": session.get('user_role', 'front_desk'),
        "action": "night_audit_completed",
        "target_type": "operational_day",
        "target_id": today_str,
        "details": f"Night audit posted. Revenue: ₹{daily_rev}, Occupancy: {occupancy_pct}%, ADR: ₹{adr}, RevPAR: ₹{revpar}"
    })

    return api_success({"message": "Night audit completed successfully.", "audit": audit_entry})

