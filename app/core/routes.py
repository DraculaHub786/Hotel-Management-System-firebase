from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    users_col, rooms_col, bookings_col, orders_col, notifications_col,
    audit_logs_col, settings_col
)
from app.auth.decorators import login_required
from app.auth.routes import get_role_redirect
from api_utils import api_success, api_error
from chatbot import get_bot_response

core_bp = Blueprint('core', __name__)

@core_bp.route('/dashboard')
@login_required
def dashboard():
    role = session.get('user_role', 'guest')
    staff_role = session.get('staff_role')
    
    # Check if this role has a dedicated portal
    if role in ['admin', 'super_admin']:
        return redirect(url_for('admin.dashboard'))
    elif role == 'manager':
        return redirect(url_for('manager.dashboard'))
    elif role == 'front_desk' or staff_role == 'front_desk':
        return redirect(url_for('frontdesk.room_board'))
    elif role in ['kitchen', 'chef'] or staff_role == 'chef':
        return redirect(url_for('dining.kitchen_queue'))
    elif role == 'housekeeping' or staff_role == 'housekeeping':
        return redirect(url_for('services.housekeeping_board'))
    elif role == 'laundry' or staff_role == 'laundry':
        return redirect(url_for('services.laundry_board'))
    elif role == 'maintenance' or staff_role == 'maintenance':
        return redirect(url_for('maintenance.work_orders'))
    elif role == 'concierge' or staff_role == 'concierge':
        return redirect(url_for('concierge.requests_board'))
    elif role == 'accountant':
        return redirect(url_for('payments.ledger'))
    elif role == 'security':
        return redirect('/staff/security')
        
    # Standard guest / member dashboard
    return render_template('dashboard.html')

@core_bp.route('/profile')
@core_bp.route('/account')
@login_required
def profile_view():
    email = session.get('user_email')
    col = users_col()
    docs = list(col.where('email', '==', email).limit(1).get())
    user_data = docs[0].to_dict() if docs else {}
    return render_template('guest/account.html', user=user_data)

@core_bp.route('/api/user/profile', methods=['GET', 'PUT', 'POST'])
@login_required
def profile_api():
    email = session.get('user_email')
    col = users_col()
    docs = list(col.where('email', '==', email).limit(1).get())
    if not docs:
        return api_error(message="User not found", status=404)

    user_doc = docs[0]
    if request.method == 'GET':
        data = user_doc.to_dict()
        data.pop('password', None)
        return api_success(data)

    body = request.get_json() or {}
    updates = {}
    if 'name' in body: updates['name'] = body['name'].strip()
    if 'phone' in body: updates['phone'] = body['phone'].strip()
    if 'preferences' in body: updates['preferences'] = body['preferences']
    
    if updates:
        user_doc.reference.update(updates)
        if 'name' in updates:
            session['user_name'] = updates['name']
            
    return api_success({"message": "Profile updated successfully"})

@core_bp.route('/notifications')
@login_required
def notifications_view():
    return render_template('guest/account.html', active_tab='notifications')

@core_bp.route('/api/notifications', methods=['GET', 'POST'])
@login_required
def notifications_api():
    email = session.get('user_email')
    role = session.get('user_role', 'guest')
    col = notifications_col()

    if request.method == 'GET':
        try:
            # Notifications targeting this email or this role
            user_notifs = [d.to_dict() for d in col.where('target_email', '==', email).stream()]
            role_notifs = [d.to_dict() for d in col.where('target_role', '==', role).stream()]
            combined = user_notifs + role_notifs
            # Sort newest first
            combined.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return api_success(combined[:50])
        except Exception as e:
            return api_success([])

    body = request.get_json() or {}
    notif = {
        "target_email": body.get('target_email', email),
        "target_role": body.get('target_role'),
        "title": body.get('title', 'Notification'),
        "message": body.get('message', ''),
        "is_read": False,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    col.add(notif)
    return api_success({"message": "Notification created"})

@core_bp.route('/search')
@login_required
def search_view():
    query = request.args.get('q', '')
    return render_template('dashboard.html', search_query=query)

@core_bp.route('/api/search', methods=['GET'])
@login_required
def search_api():
    q = request.args.get('q', '').strip().lower()
    if not q:
        return api_success({"results": []})

    results = []
    # Search Rooms
    for doc in rooms_col().stream():
        d = doc.to_dict()
        if q in str(d.get('number', '')).lower() or q in str(d.get('type', '')).lower():
            results.append({"type": "room", "title": f"Room {d.get('number')} ({d.get('type')})", "url": f"/rooms/{doc.id}"})

    # Search Bookings
    for doc in bookings_col().limit(50).stream():
        d = doc.to_dict()
        if q in str(d.get('booking_no', '')).lower() or q in str(d.get('guest_name', '')).lower():
            results.append({"type": "booking", "title": f"Booking #{d.get('booking_no')} - {d.get('guest_name')}", "url": f"/confirmation/{doc.id}"})

    return api_success({"results": results[:20]})

@core_bp.route('/help')
@core_bp.route('/support')
def help_view():
    return render_template('guest/support.html')

@core_bp.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    data = request.get_json() or {}
    user_message = data.get('message', '')
    user_email = session.get('user_email', 'guest@nur-e-haya.com')
    
    if not user_message:
        return api_error(message="Message cannot be empty", status=400)
        
    res = get_bot_response(user_message, user_email)
    return jsonify({
        "success": True,
        "response": res.get("response", "I am here to assist you with your stay at Nur-e-Haya."),
        "intent": res.get("intent", "general"),
        "suggestions": res.get("suggestions", ["Room Booking", "Dining Menu", "Housekeeping", "Check-in Times"])
    })
