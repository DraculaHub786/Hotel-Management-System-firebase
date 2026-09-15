import time
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    security_incidents_col, visitor_logs_col, parking_records_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

security_bp = Blueprint('security', __name__)

# SCR-84: Incident Reports
@security_bp.route('/staff/security', methods=['GET'])
@role_required('admin', 'manager', 'security')
def incidents_list():
    incidents = []
    for doc in security_incidents_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        incidents.append(d)
    return render_template('security/incident_list.html', incidents=incidents)

@security_bp.route('/staff/security/new', methods=['GET'])
@role_required('admin', 'manager', 'security')
def new_incident_view():
    return render_template('security/new_incident.html')

@security_bp.route('/staff/security/<incident_id>', methods=['GET'])
@role_required('admin', 'manager', 'security')
def incident_detail(incident_id):
    doc = security_incidents_col().document(str(incident_id)).get()
    idata = doc.to_dict() if doc.exists else {"id": incident_id, "type": "Noise", "severity": "low"}
    idata['id'] = incident_id
    return render_template('security/incident_detail.html', incident=idata)

@security_bp.route('/staff/security/flags', methods=['GET'])
@security_bp.route('/api/security/flags', methods=['GET'])
@role_required('admin', 'manager', 'security')
def security_flags():
    flags = [
        {"flag_type": "VIP Guest Protection", "room": "Suite 103", "status": "active"},
        {"flag_type": "Keycard Multiple Failed Access", "room": "Room 205", "status": "resolved"}
    ]
    if request.path.startswith('/api/'):
        return api_success(flags)
    return render_template('security/verification_flags.html', flags=flags)

@security_bp.route('/api/security/incidents', methods=['GET', 'POST'])
def api_incidents():
    if request.method == 'GET':
        incidents = []
        for doc in security_incidents_col().stream():
            d = doc.to_dict()
            d['id'] = doc.id
            incidents.append(d)
        return api_success(incidents)

    data = request.get_json() or {}
    type_ = data.get('type')
    desc = data.get('description', '')
    severity = data.get('severity', 'medium')
    loc = data.get('location_room_id', 'Main Lobby')

    doc_data = {
        "type": type_,
        "description": desc,
        "severity": severity,
        "location_room_id": loc,
        "reported_by": session.get('user_email', 'security_officer'),
        "status": "investigating",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    sref = security_incidents_col().add(doc_data)
    return api_success({"incident_id": sref[1].id, "message": "Security incident logged"})

@security_bp.route('/api/security/incidents/<incident_id>', methods=['PATCH', 'POST'])
@role_required('admin', 'manager', 'security')
def api_update_incident(incident_id):
    data = request.get_json() or {}
    doc = security_incidents_col().document(str(incident_id)).get()
    updates = {}
    if 'status' in data: updates['status'] = data['status']
    if 'notes' in data: updates['notes'] = data['notes']
    updates['updated_at'] = datetime.utcnow().isoformat() + "Z"

    if doc.exists:
        doc.reference.update(updates)
        rdata = doc.to_dict()
        rdata.update(updates)
    else:
        rdata = {"id": incident_id, **updates}
    return api_success(rdata)

# SCR-83: Visitor Log
@security_bp.route('/security/visitors', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'security', 'front_desk')
def visitor_log():
    if request.method == 'GET':
        logs = [d.to_dict() for d in visitor_logs_col().stream()]
        return render_template('security/visitor_log.html', visitor_logs=logs)
    
    data = request.get_json() or {}
    visitor_logs_col().add({
        "visitor_name": data.get('visitor_name'),
        "host_room": data.get('host_room'),
        "purpose": data.get('purpose', 'Personal visit'),
        "in_time": datetime.utcnow().isoformat() + "Z",
        "out_time": None
    })
    return api_success({"message": "Visitor entry recorded"})

# SCR-85: Parking Management
@security_bp.route('/security/parking', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'security')
def parking_management():
    slots = [
        {"slot_no": "P-01", "type": "Valet / VIP", "vehicle_no": "GA-01-AB-1234", "room": "Suite 103", "status": "occupied"},
        {"slot_no": "P-02", "type": "Guest Regular", "vehicle_no": "MH-02-CD-5678", "room": "Room 101", "status": "occupied"},
        {"slot_no": "P-03", "type": "EV Fast Charging", "vehicle_no": None, "room": None, "status": "available"},
        {"slot_no": "P-04", "type": "Guest Regular", "vehicle_no": None, "room": None, "status": "available"}
    ]
    return render_template('security/parking.html', parking_slots=slots)

# SCR-86: Emergency & Safety Board
@security_bp.route('/security/emergency', methods=['GET'])
def emergency_board():
    contacts = [
        {"department": "Fire Emergency", "number": "101 / +91 832 222 5555"},
        {"department": "Medical Emergency / Ambulance", "number": "108 / +91 832 242 4242"},
        {"department": "Local Police Station", "number": "100 / +91 832 222 3333"},
        {"department": "Hotel Security Command Center", "number": "Ext. 0 / +91 832 678 9000"}
    ]
    return render_template('security/emergency.html', contacts=contacts)
