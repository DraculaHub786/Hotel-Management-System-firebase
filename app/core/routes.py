import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    users_col, rooms_col, bookings_col, orders_col, notifications_col,
    audit_logs_col, settings_col, chat_history_col, concierge_requests_col
)
from app.auth.decorators import login_required
from app.auth.routes import get_role_redirect
from api_utils import api_success, api_error
from chatbot import get_bot_response

core_bp = Blueprint('core', __name__)
logger = logging.getLogger(__name__)

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
    elif role == 'waiter' or staff_role == 'waiter':
        return redirect('/dining/tables')
        
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
    user_message = data.get('message', '').strip()
    user_email = session.get('user_email', 'guest@nur-e-haya.com')
    
    if not user_message:
        return api_error(message="Message cannot be empty", status=400)
        
    res = get_bot_response(user_message, user_email)
    return jsonify({
        "success": True,
        "response": res.get("response", "I am here to assist you with your stay at Nur-e-Haya."),
        "intent": res.get("intent", "general"),
        "confidence": res.get("confidence", 0.92),
        "suggestions": res.get("suggestions", ["Spa & Massages", "Pool Timings", "Room Booking", "Dining Menu"])
    })

@core_bp.route('/api/chatbot/message', methods=['POST'])
def chatbot_message():
    """Dashboard chatbot messaging endpoint"""
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    user_email = session.get('user_email', 'guest@nur-e-haya.com')
    
    if not user_message:
        return api_error(message="Message cannot be empty", status=400)
        
    res = get_bot_response(user_message, user_email)
    bot_reply = res.get("response", "I am here to assist you with your stay at Nur-e-Haya.")
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    # Store to chat history collection for persistent conversations
    try:
        chat_history_col().add({
            "user_email": user_email,
            "user_message": user_message,
            "bot_response": bot_reply,
            "intent": res.get("intent", "general"),
            "confidence": res.get("confidence", 0.92),
            "timestamp": now_iso,
            "created_at": now_iso
        })
    except Exception as e:
        logger.warning(f"Could not persist chat history: {e}")
        
    return jsonify({
        "success": True,
        "response": bot_reply,
        "intent": res.get("intent", "general"),
        "confidence": res.get("confidence", 0.92),
        "suggestions": res.get("suggestions", ["Spa Treatments", "Pool Timings", "Room Rates", "Dining Menu"]),
        "timestamp": now_iso
    })

@core_bp.route('/api/chatbot/suggestions', methods=['GET'])
def chatbot_suggestions():
    """Returns curated starter prompts covering all facilities and services"""
    return jsonify({
        "success": True,
        "suggestions": [
            "What are your Spa treatments and rates?",
            "What are the heated rooftop pool timings?",
            "How do I book a room at Nur-e-Haya?",
            "What are check-in and check-out times?",
            "What are your dining & room service options?",
            "Tell me about the fitness center & sauna"
        ]
    })

@core_bp.route('/api/chatbot/history', methods=['GET'])
def chatbot_history():
    """Returns recent chat history for the active user"""
    user_email = session.get('user_email', 'guest@nur-e-haya.com')
    history = []
    try:
        docs = chat_history_col().where('user_email', '==', user_email).stream()
        for doc in docs:
            d = doc.to_dict()
            history.append({
                "user_message": d.get("user_message", ""),
                "bot_response": d.get("bot_response", ""),
                "timestamp": d.get("timestamp", "")
            })
        # Sort descending by timestamp, take last 15
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        history = history[:15]
    except Exception as e:
        logger.warning(f"Could not load chat history: {e}")
        
    return jsonify({
        "success": True,
        "history": history
    })

@core_bp.route('/api/chatbot/transfer', methods=['POST'])
def chatbot_transfer():
    """Handles guest escalation to live human concierge agent"""
    data = request.get_json() or {}
    user_email = session.get('user_email', 'guest@nur-e-haya.com')
    reason = data.get('reason', 'User requested human assistance')
    now_iso = datetime.utcnow().isoformat() + "Z"
    
    try:
        concierge_requests_col().add({
            "guest_email": user_email,
            "request_type": "Human Support Escalation",
            "notes": reason,
            "status": "pending",
            "priority": "high",
            "created_at": now_iso
        })
        notifications_col().add({
            "title": "Concierge Chat Escalation",
            "message": f"Guest {user_email} requested live concierge assistance.",
            "role": "concierge",
            "priority": "high",
            "unread": True,
            "created_at": now_iso
        })
    except Exception as e:
        logger.warning(f"Error logging concierge transfer: {e}")
        
    return jsonify({
        "success": True,
        "message": "Transfer request submitted to concierge."
    })

# SCR-SYNC: Real-Time Cross-Role SSE Stream
@core_bp.route('/api/sync/stream', methods=['GET'])
def sync_stream():
    import json
    import time
    from flask import Response
    from app.core.sync_hub import sync_hub

    user_role = session.get('user_role', 'guest')
    staff_role = session.get('staff_role')
    user_email = session.get('user_email')
    room_number = session.get('room_number')

    raw_channels = request.args.get('channels', 'announcements').split(',')
    requested_channels = [c.strip() for c in raw_channels if c.strip()]

    # Validate channel permissions
    allowed = set()
    for ch in requested_channels:
        if ch == 'announcements':
            allowed.add(ch)
        elif user_role in ('admin', 'super_admin', 'manager'):
            allowed.add(ch)
        elif user_role == 'guest':
            if room_number and ch == f"guest:{room_number}":
                allowed.add(ch)
            elif user_email and ch == f"guest:{user_email}":
                allowed.add(ch)
        else:
            # Staff roles
            effective_role = staff_role or user_role
            role_channel_map = {
                'front_desk': {'front_desk', 'housekeeping', 'pos'},
                'kitchen': {'kitchen', 'pos'},
                'chef': {'kitchen', 'pos'},
                'housekeeping': {'housekeeping', 'front_desk'},
                'pos': {'pos', 'kitchen'},
                'maintenance': {'maintenance'},
                'events': {'events', 'banquets'},
                'concierge': {'concierge', 'guest:*'}
            }
            permitted = role_channel_map.get(effective_role, set())
            if ch in permitted:
                allowed.add(ch)

    if not allowed:
        allowed.add('announcements')

    sub = sync_hub.subscribe(list(allowed))

    def generate_events():
        try:
            # Welcome handshake
            init_msg = json.dumps({"status": "connected", "channels": list(allowed)})
            yield f"event: connected\ndata: {init_msg}\n\n"

            while True:
                try:
                    event = sub.queue.get(timeout=15.0)
                    evt_name = event.get('event', 'message')
                    evt_id = event.get('id', '')
                    payload_json = json.dumps(event)
                    yield f"id: {evt_id}\nevent: {evt_name}\ndata: {payload_json}\n\n"
                except Exception:
                    # 15s heartbeat to maintain connection
                    yield ": ping\n\n"
        finally:
            sync_hub.unsubscribe(sub)

    resp = Response(generate_events(), mimetype='text/event-stream')
    resp.headers['Cache-Control'] = 'no-cache, no-transform'
    resp.headers['X-Accel-Buffering'] = 'no'
    resp.headers['Connection'] = 'keep-alive'
    return resp

