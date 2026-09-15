import time
import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    banquet_bookings_col, catering_packages_col, spa_bookings_col,
    pool_bookings_col, gym_bookings_col, facilities_col, notifications_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from app.events.facilities_data import FACILITIES_DATA, FACILITY_SECTIONS

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__)

# Facilities & Wellness Catalog
@events_bp.route('/facilities', methods=['GET'])
def facilities_catalog():
    try:
        facs = [d.to_dict() for d in facilities_col().stream()]
    except Exception as e:
        logger.warning(f"Error reading facilities: {e}")
        facs = []

    if not facs or len(facs) < 10:
        facs = FACILITIES_DATA

    # Ensure each item has an id
    for f in facs:
        if not f.get('id'):
            f['id'] = f.get('name', 'fac').lower().replace(' ', '_')

    return render_template(
        'guest/facilities.html',
        facilities=facs,
        sections=FACILITY_SECTIONS
    )

@events_bp.route('/facilities/<facility_id>', methods=['GET'])
def facility_detail(facility_id):
    fdata = None
    try:
        doc = facilities_col().document(str(facility_id)).get()
        if doc.exists:
            fdata = doc.to_dict()
    except Exception as e:
        logger.warning(f"Error fetching facility doc: {e}")

    if not fdata:
        for f in FACILITIES_DATA:
            if f['id'] == facility_id:
                fdata = f
                break

    if not fdata:
        fdata = FACILITIES_DATA[0]

    # Get related items in the same section
    related = [f for f in FACILITIES_DATA if f.get('section_id') == fdata.get('section_id') and f.get('id') != fdata.get('id')][:3]

    return render_template('guest/facility_detail.html', facility=fdata, related=related)

@events_bp.route('/api/facilities/book', methods=['POST'])
def api_book_facility_slot():
    """Direct API for reserving a spa or wellness facility slot"""
    data = request.get_json() or {}
    facility_id = data.get('facility_id') or data.get('ref_id')
    slot_date = data.get('date') or datetime.utcnow().strftime("%Y-%m-%d")
    slot_time = data.get('slot_time') or data.get('slot') or "10:30 AM"
    therapist = data.get('therapist', 'Master Practitioner')
    user_email = session.get('user_email', data.get('email', 'guest@nur-e-haya.com'))
    guest_name = session.get('user_name', data.get('name', 'Valued Guest'))
    room_number = session.get('room_number', data.get('room_number', '201'))

    # Locate facility metadata
    target_fac = None
    for f in FACILITIES_DATA:
        if f['id'] == facility_id:
            target_fac = f
            break
    if not target_fac:
        target_fac = {
            "id": facility_id or "fac_custom",
            "name": data.get('name', 'Spa & Wellness Session'),
            "category": "Ayurvedic Spa & Wellness",
            "price": float(data.get('unit_price', data.get('price', 2500))),
            "duration": "60 mins"
        }

    booking_no = f"SPA-{random.randint(1000, 9999)}"
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    booking_record = {
        "booking_no": booking_no,
        "facility_id": target_fac.get("id"),
        "facility_name": target_fac.get("name"),
        "treatment": target_fac.get("name"),
        "category": target_fac.get("category", "Ayurvedic Spa & Wellness"),
        "user_email": user_email,
        "guest_name": guest_name,
        "room_number": str(room_number),
        "date": slot_date,
        "slot_time": slot_time,
        "time_slot": slot_time,
        "price": float(target_fac.get("price", 2500)),
        "status": "confirmed",
        "payment_status": "confirmed",
        "therapist": therapist,
        "notes": data.get("notes", ""),
        "created_at": now_iso
    }

    # Store according to facility category
    sec_id = target_fac.get('section_id', 'spa')
    if sec_id == 'pool':
        bref = pool_bookings_col().add(booking_record)
    elif sec_id == 'fitness':
        bref = gym_bookings_col().add(booking_record)
    else:
        bref = spa_bookings_col().add(booking_record)

    # Trigger staff notification
    try:
        notifications_col().add({
            "title": f"New Facility Reservation: {target_fac.get('name')}",
            "message": f"Guest {guest_name} reserved {target_fac.get('name')} for {slot_date} at {slot_time}.",
            "role": "concierge",
            "priority": "medium",
            "unread": True,
            "created_at": now_iso
        })
    except Exception as e:
        logger.warning(f"Could not log facility notification: {e}")

    return api_success({
        "booking_id": bref[1].id if bref else booking_no,
        "booking_no": booking_no,
        "message": f"Successfully confirmed reservation for {target_fac.get('name')} on {slot_date} at {slot_time}!",
        "facility_name": target_fac.get("name"),
        "slot_date": slot_date,
        "slot_time": slot_time
    })

# SCR-59: Banquet / Hall Booking
@events_bp.route('/events/banquets', methods=['GET', 'POST'])
def banquet_booking():
    if request.method == 'GET':
        halls = [
            {"name": "Grand Kohinoor Ballroom", "capacity": 500, "rate_per_day": 125000, "features": ["LED Video Walls", "Stage", "Banqueting Hall"]},
            {"name": "Sapphire Conference Suite", "capacity": 120, "rate_per_day": 45000, "features": ["Video Conferencing", "Projectors", "Breakout Lounge"]},
            {"name": "Palm Lawn & Poolside Deck", "capacity": 350, "rate_per_day": 85000, "features": ["Open Air", "Gazebo Setup", "DJ Booth Area"]}
        ]
        return render_template('events/banquets.html', halls=halls)

    data = request.get_json() or {}
    bref = banquet_bookings_col().add({
        "hall_name": data.get('hall_name'),
        "event_date": data.get('event_date'),
        "guest_count": data.get('guest_count'),
        "user_email": session.get('user_email', data.get('email')),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"id": bref[1].id, "message": "Banquet booking inquiry submitted."})

# SCR-60: Catering Packages
@events_bp.route('/events/catering', methods=['GET'])
def catering_packages():
    packages = [
        {"name": "Royal Feast Banquet", "price_per_plate": 1800, "items": ["3 Live Counters", "4 Starters", "6 Mains", "4 Desserts"]},
        {"name": "Corporate High Tea & Lunch", "price_per_plate": 1100, "items": ["Artisanal Sandwiches", "Canapés", "3 Mains", "Coffee Bar"]},
        {"name": "Cocktail & Tapas Soiree", "price_per_plate": 2200, "items": ["Live Barbecue", "Gourmet Tapas", "Cheese Board", "Craft Mocktails"]}
    ]
    return render_template('events/catering.html', packages=packages)

# SCR-61: Events Calendar
@events_bp.route('/events/calendar', methods=['GET'])
@role_required('admin', 'manager', 'front_desk', 'events')
def events_calendar():
    events = [d.to_dict() for d in banquet_bookings_col().stream()]
    return render_template('events/calendar.html', events=events)

# SCR-62 / SCR-63: Spa & Fitness Booking
@events_bp.route('/wellness/spa', methods=['GET', 'POST'])
@login_required
def spa_booking():
    if request.method == 'GET':
        return render_template('events/spa.html')
    data = request.get_json() or {}
    spa_bookings_col().add({
        "treatment": data.get('treatment', 'Full Body Ayurvedic Massage'),
        "slot_time": data.get('slot_time'),
        "user_email": session.get('user_email'),
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"message": "Spa session reserved successfully!"})

@events_bp.route('/wellness/fitness', methods=['GET', 'POST'])
@login_required
def pool_gym_booking():
    if request.method == 'GET':
        return render_template('events/fitness.html')
    data = request.get_json() or {}
    pool_bookings_col().add({
        "facility": data.get('facility', 'pool'),
        "time_slot": data.get('time_slot'),
        "user_email": session.get('user_email'),
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"message": "Fitness session booked."})

# SCR-64: Event Enquiry Inbox
@events_bp.route('/events/enquiries', methods=['GET'])
@role_required('admin', 'manager', 'front_desk')
def enquiries_inbox():
    enquiries = [d.to_dict() for d in banquet_bookings_col().stream()]
    return render_template('events/enquiries.html', enquiries=enquiries)
