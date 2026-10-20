"""
test_security_and_ux_patches.py - Verification suite for security, IDOR, CSRF, and route fixes
"""
import pytest
from app import create_app
from app.firebase_db import bookings_col, invoices_col, chat_history_col

@pytest.fixture
def app_instance():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-verification-secret'
    return app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_notifications_view_resolves_cleanly(client):
    """Verify /notifications renders 200 without Jinja UndefinedError."""
    with client.session_transaction() as sess:
        sess['user_email'] = 'test.guest@example.com'
        sess['user_role'] = 'guest'
        sess['user_name'] = 'Test Guest'

    resp = client.get('/notifications')
    assert resp.status_code == 200
    assert b'Account' in resp.data or b'notification' in resp.data.lower()

def test_booking_detail_route_loads_template(client):
    """Verify /my-bookings/<id> resolves and renders booking_detail.html."""
    booking_id = "bk_test_detail_991"
    bookings_col().document(booking_id).set({
        "id": booking_id,
        "booking_no": "BK-991-TEST",
        "user_email": "booking.owner@example.com",
        "room_number": "301",
        "room_name": "Royal Wing Suite",
        "status": "confirmed",
        "check_in": "2026-11-01",
        "check_out": "2026-11-05",
        "total_price": 12000.0,
        "items": [{"name": "Royal Wing Suite", "qty": 1, "unit_price": 12000.0, "line_total": 12000.0}]
    })

    # 1. Owner can access
    with client.session_transaction() as sess:
        sess['user_email'] = 'booking.owner@example.com'
        sess['user_role'] = 'guest'

    resp = client.get(f'/my-bookings/{booking_id}')
    assert resp.status_code == 200
    assert b'Royal Wing Suite' in resp.data

    # 2. Another non-staff guest gets rejected
    with client.session_transaction() as sess:
        sess['user_email'] = 'intruder@example.com'
        sess['user_role'] = 'guest'

    resp_denied = client.get(f'/my-bookings/{booking_id}')
    assert resp_denied.status_code in [403, 404]

def test_invoice_idor_protection(client):
    """Verify guest cannot access another guest's invoice."""
    inv_id = "inv_private_777"
    invoices_col().document(inv_id).set({
        "invoice_no": f"INV-{inv_id}",
        "user_email": "rich.guest@example.com",
        "guest_name": "Sir Sterling",
        "total": 55000.0,
        "status": "PAID"
    })

    # Non-owner guest attempt
    with client.session_transaction() as sess:
        sess['user_email'] = 'random.guest@example.com'
        sess['user_role'] = 'guest'

    resp = client.get(f'/accounts/invoices/{inv_id}')
    assert resp.status_code == 403

def test_anonymous_chat_isolation(client):
    """Verify two anonymous clients do not share chat history."""
    client1 = client
    client1.get('/') # Initialize session 1
    
    # Client 1 posts a message
    res1 = client1.post('/api/chatbot/message', json={"message": "My private query 1"})
    assert res1.status_code == 200
    
    # Client 1 reads history
    hist1 = client1.get('/api/chatbot/history').get_json()['history']
    assert any(h['user_message'] == "My private query 1" for h in hist1)

    # Client 2 (new session) should not see Client 1's history
    with client.session_transaction() as sess:
        sess.clear()

    res2 = client.get('/api/chatbot/history').get_json()['history']
    assert not any(h['user_message'] == "My private query 1" for h in res2)
