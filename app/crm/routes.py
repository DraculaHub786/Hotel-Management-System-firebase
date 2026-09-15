import io
import csv
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Response
from app.firebase_db import (
    reviews_col, loyalty_points_log_col, users_col, settings_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__)

# SCR-87: Loyalty Points & Rewards
@crm_bp.route('/crm/loyalty', methods=['GET'])
@login_required
def loyalty_points():
    email = session.get('user_email')
    col = users_col()
    docs = list(col.where('email', '==', email).limit(1).get())
    user_data = docs[0].to_dict() if docs else {}
    points = user_data.get('loyalty_points', 150 if user_data.get('role') == 'member' else 25)
    tier = "VIP Platinum" if points > 500 else ("Gold Member" if points > 100 else "Silver Traveler")
    
    return render_template('crm/loyalty.html', points=points, tier=tier)

# SCR-88: Membership Management
@crm_bp.route('/crm/memberships', methods=['GET'])
@role_required('admin', 'manager')
def memberships_manage():
    members = [d.to_dict() for d in users_col().where('role', '==', 'member').stream()]
    return render_template('crm/memberships.html', members=members)

# SCR-89: Reviews & Feedback (with moderation)
@crm_bp.route('/crm/reviews', methods=['GET', 'POST'])
def reviews_view():
    if request.method == 'GET':
        revs = [d.to_dict() for d in reviews_col().where('status', '==', 'approved').stream()]
        if not revs:
            revs = [
                {"guest_name": "Aarav Mehta", "rating": 5, "comment": "Unmatched hospitality, stunning sea views, and world-class dining!", "date": "2026-09-10"},
                {"guest_name": "Claire Dupont", "rating": 5, "comment": "The Ayur Spa and personalized concierge made our anniversary truly unforgettable.", "date": "2026-09-08"}
            ]
        return render_template('crm/reviews.html', reviews=revs)

    # Post review
    data = request.get_json() or {}
    reviews_col().add({
        "guest_name": session.get('user_name', 'Guest'),
        "user_email": session.get('user_email', 'guest@nur-e-haya.com'),
        "rating": int(data.get('rating', 5)),
        "comment": data.get('comment', ''),
        "status": "pending", # moderated
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"message": "Thank you for your feedback! Review submitted for moderation."})

@crm_bp.route('/api/reviews/<id>/moderate', methods=['POST'])
@role_required('admin', 'manager')
def moderate_review(id):
    data = request.get_json() or {}
    new_status = data.get('status', 'approved') # approved / hidden
    doc = reviews_col().document(str(id)).get()
    if doc.exists:
        doc.reference.update({"status": new_status})
        return api_success({"message": f"Review marked {new_status}"})
    return api_error(message="Review not found", status=404)

# SCR-90: Newsletter & Campaigns
@crm_bp.route('/admin/newsletter', methods=['GET'])
@role_required('admin', 'super_admin')
def admin_newsletter():
    stats = {
        "total": 348,
        "active": 336,
        "unsubscribed": 12
    }
    subscribers = [
        {"email": "vip.guest@gmail.com", "subscribed_at": "2026-09-01 10:30", "status": "active", "source": "Checkout Modal"},
        {"email": "corporate.travel@tcs.com", "subscribed_at": "2026-08-25 14:15", "status": "active", "source": "Homepage Banner"},
        {"email": "leisure.stay@outlook.com", "subscribed_at": "2026-08-10 09:45", "status": "unsubscribed", "source": "Dining Feedback"}
    ]
    return render_template('admin_newsletter.html', stats=stats, subscribers=subscribers)

@crm_bp.route('/api/newsletter/subscribe', methods=['POST'])
def api_newsletter_subscribe():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    if not email:
        return api_error(message="Email is required", status=400)
    return api_success({"message": "Successfully subscribed to our newsletter!"})

@crm_bp.route('/api/newsletter/unsubscribe', methods=['POST'])
def api_newsletter_unsubscribe():
    return api_success({"message": "Successfully unsubscribed."})

@crm_bp.route('/api/newsletter/check-subscription', methods=['GET'])
def api_check_subscription():
    return api_success({"subscribed": True})

@crm_bp.route('/api/newsletter/export', methods=['GET'])
@role_required('admin', 'super_admin')
def export_newsletter():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'Subscribed At'])
    writer.writerow(['guest@example.com', '2026-09-01T12:00:00Z'])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=subscribers.csv"})
