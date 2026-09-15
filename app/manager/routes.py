import io
import csv
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Response
from app.firebase_db import (
    rooms_col, bookings_col, transactions_col, housekeeping_tasks_col,
    maintenance_tickets_col, announcements_col, settings_col, users_col
)
from app.auth.decorators import role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

manager_bp = Blueprint('manager', __name__)

# SCR-65: Manager Dashboard
@manager_bp.route('/manager', methods=['GET'])
@role_required('admin', 'manager')
def dashboard():
    total_rooms = len(list(rooms_col().stream()))
    occupied_rooms = len(list(rooms_col().where('status', '==', 'occupied').stream()))
    cleaning_rooms = len(list(rooms_col().where('status', '==', 'cleaning').stream()))
    occupancy_pct = round((occupied_rooms / total_rooms * 100), 1) if total_rooms else 0

    # Today's revenue
    today_str = datetime.utcnow().date().isoformat()
    today_rev = 0.0
    for tx in transactions_col().stream():
        d = tx.to_dict()
        if d.get('created_at', '').startswith(today_str):
            today_rev += float(d.get('amount', 0))

    # Active tasks
    hsk_tasks = len(list(housekeeping_tasks_col().where('status', 'in', ['pending', 'in_progress']).stream()))
    maint_tasks = len(list(maintenance_tickets_col().where('status', '==', 'open').stream()))

    stats = {
        "occupancy_pct": occupancy_pct,
        "occupied_rooms": occupied_rooms,
        "cleaning_rooms": cleaning_rooms,
        "total_rooms": total_rooms,
        "today_revenue": round(today_rev, 2),
        "active_hsk_tasks": hsk_tasks,
        "active_maint_tasks": maint_tasks,
        "pending_payments": 2
    }
    return render_template('manager/dashboard.html', stats=stats)

# SCR-66: Staff Task Assignment Console
@manager_bp.route('/manager/tasks/assign', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def task_assignment():
    if request.method == 'GET':
        tasks = [d.to_dict() for d in housekeeping_tasks_col().where('status', '==', 'pending').stream()]
        staff = [d.to_dict() for d in users_col().where('role', 'in', ['housekeeping', 'laundry', 'maintenance']).stream()]
        return render_template('manager/task_assignment.html', pending_tasks=tasks, staff_members=staff)

    data = request.get_json() or {}
    task_id = data.get('task_id')
    staff_email = data.get('staff_email')
    
    doc = housekeeping_tasks_col().document(str(task_id)).get()
    if doc.exists:
        doc.reference.update({"assigned_to": staff_email, "status": "assigned"})
        return api_success({"message": f"Task assigned to {staff_email}"})
    return api_error(message="Task not found", status=404)

# SCR-67: Rooms & Rate Management
@manager_bp.route('/manager/rates', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def rate_management():
    if request.method == 'GET':
        rooms = [d.to_dict() for d in rooms_col().stream()]
        return render_template('manager/rate_management.html', rooms=rooms)

    data = request.get_json() or {}
    room_id = data.get('room_id')
    new_price = float(data.get('price', 3500))
    doc = rooms_col().document(str(room_id)).get()
    if doc.exists:
        doc.reference.update({"price": new_price})
        return api_success({"message": "Base rate updated"})
    return api_error(message="Room not found", status=404)

# SCR-68: Availability Calendar
@manager_bp.route('/manager/calendar', methods=['GET'])
@role_required('admin', 'manager')
def availability_calendar():
    rooms = [d.to_dict() for d in rooms_col().stream()]
    bookings = [d.to_dict() for d in bookings_col().limit(100).stream()]
    return render_template('manager/availability_calendar.html', rooms=rooms, bookings=bookings)

# SCR-69: Operations Reports + CSV Export
@manager_bp.route('/manager/reports', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def operations_reports():
    format_type = request.args.get('format', 'html')
    
    if format_type == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Booking No', 'Guest Name', 'Room', 'Check In', 'Check Out', 'Total Price', 'Status'])
        for doc in bookings_col().stream():
            b = doc.to_dict()
            writer.writerow([
                b.get('booking_no', ''),
                b.get('guest_name', ''),
                b.get('room_number', ''),
                b.get('check_in', ''),
                b.get('check_out', ''),
                b.get('total_price', 0),
                b.get('status', '')
            ])
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=hotel_operations_report.csv"}
        )

    return render_template('admin/revenue_dashboard.html', is_reports=True)

# SCR-70: Announcements / Broadcasts
@manager_bp.route('/manager/announcements', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def announcements():
    if request.method == 'GET':
        posts = [d.to_dict() for d in announcements_col().order_by('created_at', direction='DESCENDING').stream()]
        return render_template('manager/broadcasts.html', announcements=posts)

    data = request.get_json() or {}
    announcements_col().add({
        "title": data.get('title'),
        "message": data.get('message'),
        "target_role": data.get('target_role', 'all'),
        "posted_by": session.get('user_email'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"message": "Announcement broadcasted successfully."})

# SCR-71: Staff Shifts & Attendance
@manager_bp.route('/manager/shifts', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def staff_shifts():
    shifts = [
        {"staff_name": "Ravi Kumar", "department": "Housekeeping", "shift": "Morning (07:00 - 15:30)", "status": "On Duty"},
        {"staff_name": "Pooja Sharma", "department": "Front Desk", "shift": "General (09:00 - 18:00)", "status": "On Duty"},
        {"staff_name": "Chef Anthony", "department": "Kitchen", "shift": "Evening (14:00 - 23:00)", "status": "Scheduled"},
        {"staff_name": "Suresh Patel", "department": "Maintenance", "shift": "Night (23:00 - 07:00)", "status": "Off Duty"}
    ]
    return render_template('manager/shifts.html', shifts=shifts)

# SCR-72: Expense Approvals
@manager_bp.route('/manager/expenses', methods=['GET', 'POST'])
@role_required('admin', 'manager')
def expense_approvals():
    expenses = [
        {"expense_id": "EXP-101", "department": "Kitchen", "item": "Imported Olive Oil & Herbs", "amount": 4200, "status": "pending"},
        {"expense_id": "EXP-102", "department": "Maintenance", "item": "Emergency AC Compressor Valves", "amount": 8500, "status": "approved"},
        {"expense_id": "EXP-103", "department": "Housekeeping", "item": "Eco-friendly Linen Detergent Drums", "amount": 6300, "status": "pending"}
    ]
    return render_template('manager/expenses.html', expenses=expenses)
