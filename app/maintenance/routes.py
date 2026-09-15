import time
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import maintenance_tickets_col, maintenance_orders_col, assets_col
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

maintenance_bp = Blueprint('maintenance', __name__)

# SCR-44: Work Order Queue
@maintenance_bp.route('/staff/maintenance', methods=['GET'])
@maintenance_bp.route('/maintenance/work-orders', methods=['GET'])
@role_required('admin', 'manager', 'maintenance')
def work_orders():
    tickets = []
    for doc in maintenance_tickets_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        tickets.append(d)
    return render_template('maintenance/ticket_queue.html', tickets=tickets)

@maintenance_bp.route('/staff/maintenance/tickets/<ticket_id>', methods=['GET'])
@role_required('admin', 'manager', 'maintenance')
def ticket_detail(ticket_id):
    doc = maintenance_tickets_col().document(str(ticket_id)).get()
    tdata = doc.to_dict() if doc.exists else {"id": ticket_id, "status": "open", "issue_type": "HVAC", "priority": "high"}
    tdata['id'] = ticket_id
    return render_template('maintenance/ticket_detail.html', ticket=tdata)

@maintenance_bp.route('/api/maintenance/tickets', methods=['GET', 'POST'])
def api_maintenance_tickets():
    if request.method == 'GET':
        tickets = [d.to_dict() for d in maintenance_tickets_col().stream()]
        return api_success(tickets)

    data = request.get_json() or {}
    tref = maintenance_tickets_col().add({
        "issue_type": data.get('issue_type', 'general'),
        "description": data.get('description', ''),
        "priority": data.get('priority', 'medium'),
        "location": data.get('location', 'Hotel Main Building'),
        "status": data.get('status', 'open'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"ticket_id": tref[1].id, "message": "Ticket created"})

@maintenance_bp.route('/api/maintenance/tickets/<ticket_id>', methods=['PATCH', 'POST'])
def api_update_ticket(ticket_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    resolution_note = data.get('resolution_note', data.get('resolution_notes', ''))

    if new_status == 'resolved' and not str(resolution_note).strip():
        return api_error(message="Resolution note is required when resolving a ticket.", status=400)

    doc = maintenance_tickets_col().document(str(ticket_id)).get()
    
    updates = {}
    if 'status' in data: updates['status'] = data['status']
    if resolution_note: updates['resolution_note'] = resolution_note
    if 'assigned_to' in data: updates['assigned_to'] = data['assigned_to']
    updates['updated_at'] = datetime.utcnow().isoformat() + "Z"

    if doc.exists:
        doc.reference.update(updates)
        rdata = doc.to_dict()
        rdata.update(updates)
    else:
        rdata = {"id": ticket_id, **updates}

    return api_success(rdata)

# SCR-45: Preventive Maintenance Calendar
@maintenance_bp.route('/maintenance/preventive', methods=['GET'])
@role_required('admin', 'manager', 'maintenance')
def preventive_calendar():
    schedules = [
        {"system": "Central HVAC & Chillers", "frequency": "Monthly", "next_due": "2026-10-01", "assigned_lead": "Prakash Nair", "status": "scheduled"},
        {"system": "Elevators & Escalators", "frequency": "Bi-weekly", "next_due": "2026-09-20", "assigned_lead": "Otis Tech", "status": "in_progress"},
        {"system": "Diesel Generator Backup", "frequency": "Monthly", "next_due": "2026-09-25", "assigned_lead": "Chief Engineer", "status": "scheduled"},
        {"system": "Water Filtration & Plumbing", "frequency": "Quarterly", "next_due": "2026-11-15", "assigned_lead": "Plumbing Team", "status": "scheduled"}
    ]
    return render_template('maintenance/preventive.html', schedules=schedules, preventive_schedules=schedules)

# SCR-46: Asset Register
@maintenance_bp.route('/maintenance/assets', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'maintenance')
def asset_register():
    assets = [d.to_dict() for d in assets_col().stream()]
    if not assets:
        assets = [
            {"asset_id": "AST-001", "name": "Daikin VRV Chiller Unit", "location": "Rooftop North", "serial": "DK-88902", "installed": "2024-02-10", "warranty_until": "2029-02-10"},
            {"asset_id": "AST-002", "name": "Cummins 250kVA Generator", "location": "Basement Power Room", "serial": "CM-44120", "installed": "2023-11-15", "warranty_until": "2028-11-15"},
            {"asset_id": "AST-003", "name": "Schindler Smart Passenger Elevator 1", "location": "East Wing Shaft", "serial": "SCH-9901", "installed": "2023-08-01", "warranty_until": "2028-08-01"}
        ]
    return render_template('maintenance/assets.html', assets=assets)

