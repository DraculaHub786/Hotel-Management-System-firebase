import time
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import concierge_requests_col
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

concierge_bp = Blueprint('concierge', __name__)

# SCR-48: Concierge Request Form & Queue
@concierge_bp.route('/staff/concierge', methods=['GET'])
@concierge_bp.route('/concierge/queue', methods=['GET'])
@role_required('admin', 'manager', 'concierge')
def requests_board():
    requests = []
    for doc in concierge_requests_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        requests.append(d)
    requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return render_template('housekeeping/task_board.html', concierge_requests=requests, is_concierge=True)

@concierge_bp.route('/concierge/request', methods=['GET', 'POST'])
@login_required
def request_form():
    if request.method == 'GET':
        return render_template('concierge/request_form.html')

    data = request.get_json() or {}
    req_type = data.get('type', 'wake_up') # wake_up, taxi, transfer, tour, doctor
    cdoc = {
        "request_no": f"CR{int(time.time())}",
        "user_email": session.get('user_email'),
        "guest_name": session.get('user_name'),
        "room_number": data.get('room_number', '101'),
        "type": req_type,
        "details": data.get('details', ''),
        "scheduled_time": data.get('scheduled_time'),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    cref = concierge_requests_col().add(cdoc)
    return api_success({"request_id": cref[1].id, "message": "Concierge request logged. Our team is arranging it."})

@concierge_bp.route('/api/concierge/requests', methods=['GET', 'POST'])
def api_concierge_requests():
    if request.method == 'GET':
        reqs = [d.to_dict() for d in concierge_requests_col().stream()]
        return api_success(reqs)

    data = request.get_json() or {}
    cref = concierge_requests_col().add(data)
    return api_success({"id": cref[1].id, "message": "Request created"})

@concierge_bp.route('/api/concierge/<id>/status', methods=['POST', 'PATCH'])
@role_required('admin', 'manager', 'concierge')
def api_concierge_status(id):
    data = request.get_json() or {}
    doc = concierge_requests_col().document(str(id)).get()
    if doc.exists:
        doc.reference.update({"status": data.get('status', 'completed')})
        return api_success({"message": "Status updated"})
    return api_error(message="Request not found", status=404)

# SCR-49: Airport Transfers Board
@concierge_bp.route('/concierge/transfers', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'concierge')
def airport_transfers():
    transfers = [
        {"guest_name": "Eleanor Vance", "flight_no": "AI-102", "arrival_time": "14:30", "car": "Mercedes E-Class", "driver": "Anil", "status": "assigned"},
        {"guest_name": "Vikram Sethi", "flight_no": "6E-442", "arrival_time": "17:15", "car": "Innova Crysta", "driver": "Ramesh", "status": "pending"},
        {"guest_name": "Sophia Zhang", "flight_no": "BA-139", "arrival_time": "20:45", "car": "BMW 5 Series", "driver": "Sanjay", "status": "confirmed"}
    ]
    return render_template('concierge/transfers_board.html', transfers=transfers)

# SCR-50: Tours & Activities
@concierge_bp.route('/concierge/tours', methods=['GET'])
def tours_activities():
    tours = [
        {"title": "Historical City Heritage Walk", "duration": "3 hours", "price": 1200, "image": "/static/images/luxury-room.jpg", "departure": "09:00 AM"},
        {"title": "Sunset Catamaran Luxury Cruise", "duration": "2.5 hours", "price": 3500, "image": "/static/images/suite-room.webp", "departure": "05:00 PM"},
        {"title": "Spice Plantation & Cuisine Trail", "duration": "Full Day", "price": 2800, "image": "/static/images/double-room.webp", "departure": "08:30 AM"}
    ]
    return render_template('concierge/tours.html', tours=tours)

# SCR-51: Doctor on Call
@concierge_bp.route('/concierge/doctor', methods=['GET', 'POST'])
def doctor_on_call():
    doctors = [
        {"name": "Dr. Sarah D'Souza", "specialty": "General Medicine", "phone": "+91 98230 11223", "available": "24/7 on call"},
        {"name": "Dr. Rajesh Kulkarni", "specialty": "Pediatrics", "phone": "+91 98230 44556", "available": "08:00 - 20:00"}
    ]
    return render_template('concierge/doctor.html', doctors=doctors)

# SCR-52: Local Guide
@concierge_bp.route('/concierge/local-guide', methods=['GET'])
def local_guide():
    places = [
        {"name": "Old Latin Quarter (Fontainhas)", "category": "Heritage & Architecture", "distance": "2.5 km"},
        {"name": "Fisherman's Wharf Fine Dining", "category": "Coastal Cuisine", "distance": "4.0 km"},
        {"name": "Reis Magos Fort", "category": "Historic Landmark", "distance": "6.2 km"}
    ]
    return render_template('concierge/local_guide.html', places=places)
