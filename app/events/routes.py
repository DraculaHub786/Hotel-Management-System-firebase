import time
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    banquet_bookings_col, catering_packages_col, spa_bookings_col,
    pool_bookings_col, gym_bookings_col, facilities_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

events_bp = Blueprint('events', __name__)

# Facilities & Wellness (C.8 Spec)
@events_bp.route('/facilities', methods=['GET'])
def facilities_catalog():
    facs = [d.to_dict() for d in facilities_col().stream()]
    if not facs:
        facs = [
            {"id": "spa", "name": "The Royal Ayur Spa", "category": "Wellness", "price": 2500, "image": "/static/images/luxury-room.jpg", "description": "Holistic treatments, herbal sauna, and steam bath."},
            {"id": "pool", "name": "Infinity Sky Pool", "category": "Recreation", "price": 0, "image": "/static/images/suite-room.webp", "description": "Temperature controlled panoramic rooftop pool."},
            {"id": "gym", "name": "FitLife Gymnasium", "category": "Fitness", "price": 0, "image": "/static/images/double-room.webp", "description": "High-tech cardio, strength, and personal trainer zone."}
        ]
    return render_template('guest/facilities.html', facilities=facs)

@events_bp.route('/facilities/<facility_id>', methods=['GET'])
def facility_detail(facility_id):
    doc = facilities_col().document(str(facility_id)).get()
    fdata = doc.to_dict() if doc.exists else {"name": "Spa & Wellness", "category": "Wellness", "price": 2500}
    return render_template('guest/facility_detail.html', facility=fdata)

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
