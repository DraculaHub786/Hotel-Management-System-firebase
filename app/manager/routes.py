import io
import csv
import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Response
from app.firebase_db import (
    rooms_col, bookings_col, transactions_col, housekeeping_tasks_col,
    maintenance_tickets_col, announcements_col, settings_col, users_col,
    resolve_room_doc
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from app.core.sync_hub import sync_hub

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
    doc = resolve_room_doc(room_id)
    if doc and doc.exists:
        doc.reference.update({"price": new_price})
        return api_success({"message": "Base rate updated"})
    return api_error(message="Room not found", status=404)

# SCR-68: Availability Calendar
@manager_bp.route('/manager/calendar', methods=['GET'])
@role_required('admin', 'manager')
def availability_calendar():
    rooms = [d.to_dict() for d in rooms_col().stream()]
    rooms.sort(key=lambda r: str(r.get('number', '')))

    bookings = [d.to_dict() for d in bookings_col().limit(200).stream()]
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    days_labels = [
        {"key": d.strftime("%Y-%m-%d"), "label": "Today" if i == 0 else f"+{i}d ({d.strftime('%b %d')})"}
        for i, d in enumerate(days)
    ]

    calendar_matrix = []
    for r in rooms:
        r_num = str(r.get('number', ''))
        row = {
            "number": r_num,
            "type": r.get('type', 'Deluxe Room'),
            "status": r.get('status', 'available'),
            "days": []
        }
        for d in days:
            d_str = d.strftime("%Y-%m-%d")
            is_occupied = False
            booking_match = None
            for b in bookings:
                if str(b.get('room_number', '')) == r_num and b.get('status') in ('confirmed', 'checked_in', 'active', 'booked'):
                    cin = str(b.get('check_in', ''))[:10]
                    cout = str(b.get('check_out', ''))[:10]
                    if cin and cout:
                        if cin <= d_str < cout or (cin == d_str == cout):
                            is_occupied = True
                            booking_match = b
                            break

            if d == today and r.get('status') == 'occupied':
                is_occupied = True

            if is_occupied:
                status_text = "Booked"
                status_class = "status-occupied"
            elif d == today and r.get('status') == 'maintenance':
                status_text = "Maintenance"
                status_class = "status-maintenance"
            else:
                status_text = "Available"
                status_class = "status-available"

            row["days"].append({
                "date": d_str,
                "status": status_text,
                "class": status_class,
                "guest": booking_match.get('guest_name', '') if booking_match else ''
            })
        calendar_matrix.append(row)

    return render_template('manager/availability_calendar.html', rooms=rooms, days_labels=days_labels, matrix=calendar_matrix)

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
@role_required('admin', 'manager', 'super_admin')
def announcements():
    if request.method == 'GET':
        posts = []
        try:
            for d in announcements_col().stream():
                item = d.to_dict()
                item['id'] = d.id
                posts.append(item)
            posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            logger.warning(f"Error fetching announcements: {e}")
        return render_template('manager/broadcasts.html', announcements=posts)

    data = request.get_json() or {}
    new_doc = {
        "title": data.get('title'),
        "message": data.get('message'),
        "target_role": data.get('target_role', 'all'),
        "priority": data.get('priority', 'normal'),
        "posted_by": session.get('user_name', session.get('user_email', 'Management')),
        "posted_by_email": session.get('user_email'),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    announcements_col().add(new_doc)
    try:
        sync_hub.publish('announcements', 'new_announcement', new_doc)
    except Exception as e:
        logger.warning(f"Failed to publish announcement sync: {e}")
    return api_success({"message": "Announcement broadcasted successfully."})

@manager_bp.route('/api/announcements/active', methods=['GET'])
@login_required
def api_active_announcements():
    user_role = session.get('user_role', 'guest')
    user_email = session.get('user_email', '')
    active = []
    now = datetime.utcnow()
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    try:
        for d in announcements_col().stream():
            item = d.to_dict()
            item['id'] = d.id

            # Filter already read by this user
            read_by = item.get('read_by', [])
            if user_email and user_email in read_by:
                continue

            # Expiry check: ignore older than 7 days or past explicit expires_at
            created_at = item.get('created_at', '')
            if created_at and created_at < seven_days_ago and not item.get('priority') == 'urgent':
                continue
            expires_at = item.get('expires_at')
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
                    if now > exp_dt:
                        continue
                except Exception:
                    pass

            target = str(item.get('target_role', 'all')).lower()
            u_role = str(user_role).lower()

            # Role match evaluation
            matches = False
            if target in ['all', '', 'everyone', 'all_staff']:
                matches = True
            elif target == u_role:
                matches = True
            elif u_role in ['guest', 'member', 'vip', 'user'] and target in ['guest', 'guests', 'member', 'vip']:
                matches = True
            elif u_role in ['super_admin', 'admin', 'manager']:
                matches = True  # Admins and managers see all broadcasts
            elif u_role in ['housekeeping', 'laundry'] and target in ['housekeeping', 'laundry']:
                matches = True
            elif u_role in ['kitchen', 'chef', 'waiter', 'room_service'] and target in ['kitchen', 'dining']:
                matches = True

            if matches:
                active.append(item)

        active.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    except Exception as e:
        logger.warning(f"Error streaming active announcements: {e}")

    return api_success(active[:15])

@manager_bp.route('/api/announcements/<announcement_id>/read', methods=['POST'])
@login_required
def api_mark_announcement_read(announcement_id):
    user_email = session.get('user_email')
    doc = announcements_col().document(str(announcement_id)).get()
    if doc.exists:
        data = doc.to_dict()
        read_by = data.get('read_by', [])
        if user_email and user_email not in read_by:
            read_by.append(user_email)
            doc.reference.update({"read_by": read_by})
        return api_success({"message": "Marked as read", "announcement_id": announcement_id})
    return api_error(message="Announcement not found", status=404)

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
