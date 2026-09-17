import pytest
import json
from app import create_app
from app.firebase_db import (
    get_db, rooms_col, menu_col, users_col, bookings_col,
    banquet_bookings_col, restaurant_tables_col,
    resolve_room_doc, resolve_menu_item_doc
)
from google.cloud.exceptions import NotFound
from app.core.sync_hub import sync_hub
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            yield client

# ---------------------------------------------------------
# Part 0: Data Layer & Bug Fixes
# ---------------------------------------------------------

def test_mock_firestore_raises_not_found():
    """0.2: MockDocumentReference.update() raises NotFound if doc does not exist."""
    db = get_db()
    non_existent = db.collection("rooms").document("non_existent_doc_12345")
    with pytest.raises(NotFound):
        non_existent.update({"status": "cleaning"})

def test_resolve_room_doc():
    """0.1: resolve_room_doc resolves flat codes, prefixed keys, and raw room numbers."""
    rooms_col().document("rm_HW-101").set({
        "number": "101",
        "room_number": "HW-101",
        "status": "occupied"
    })

    # Query with rm_ prefix
    doc1 = resolve_room_doc("rm_HW-101")
    assert doc1 is not None and doc1.exists
    assert doc1.to_dict()["number"] == "101"

    # Query with flat code HW-101
    doc2 = resolve_room_doc("HW-101")
    assert doc2 is not None and doc2.exists
    assert doc2.id == "rm_HW-101"

    # Query with room number 101
    doc3 = resolve_room_doc("101")
    assert doc3 is not None and doc3.exists

def test_resolve_menu_item_doc():
    """0.3: resolve_menu_item_doc resolves both padded item_001 and unpadded item_1."""
    menu_col().document("item_1").set({
        "id": "item_1",
        "name": "Zafrani Chai",
        "is_available": True
    })

    doc1 = resolve_menu_item_doc("item_1")
    assert doc1 is not None and doc1.exists
    assert doc1.to_dict()["name"] == "Zafrani Chai"

    doc2 = resolve_menu_item_doc("item_001")
    assert doc2 is not None and doc2.exists

def test_frontdesk_mark_clean_endpoint(client):
    """0.6: POST /api/front-desk/mark-clean updates canonical room status to available."""
    rooms_col().document("rm_HW-205").set({
        "number": "205",
        "room_number": "HW-205",
        "status": "cleaning"
    })

    with client.session_transaction() as sess:
        sess['user_email'] = 'admin@nur-e-haya.com'
        sess['user_role'] = 'admin'

    res = client.post('/api/front-desk/mark-clean', json={"room_id": "rm_HW-205"})
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("ok") is True or data.get("success") is True

    updated = rooms_col().document("rm_HW-205").get()
    assert updated.to_dict()["status"] == "available"

def test_menu_availability_toggle(client):
    """0.6: PATCH /api/menu-items/<id>/availability flips is_available."""
    menu_col().document("item_42").set({
        "id": "item_42",
        "name": "Royal Biryani",
        "is_available": True
    })

    with client.session_transaction() as sess:
        sess['user_email'] = 'chef@nur-e-haya.com'
        sess['user_role'] = 'chef'

    res = client.patch('/api/menu-items/item_42/availability', json={"available": False})
    assert res.status_code == 200
    res_data = res.get_json()["data"]
    assert (res_data.get("is_available") is False) or (res_data.get("available") is False)

    updated = menu_col().document("item_42").get()
    assert (updated.to_dict().get("is_available") is False) or (updated.to_dict().get("available") is False)

# ---------------------------------------------------------
# Part 1: Security Fixes
# ---------------------------------------------------------

def test_simulate_pay_requires_authentication(client):
    """Part 1.2: /api/transactions/<txn_id>/simulate-pay requires login."""
    res = client.post('/api/transactions/TXN99999/simulate-pay')
    # Should redirect to login or return 401
    assert res.status_code in (401, 302)

def test_simulate_pay_authorization(client):
    """Part 1.2: simulate-pay authorized for owner or staff."""
    from app.firebase_db import transactions_col
    transactions_col().document("TXN_TEST_1").set({
        "transaction_id": "TXN_TEST_1",
        "user_email": "guest.legit@example.com",
        "amount": 5000,
        "status": "pending"
    })

    # Unauthorized guest attempt
    with client.session_transaction() as sess:
        sess['user_email'] = 'attacker@example.com'
        sess['user_role'] = 'guest'

    res = client.post('/api/transactions/TXN_TEST_1/simulate-pay')
    assert res.status_code == 403

    # Authorized guest owner attempt
    with client.session_transaction() as sess:
        sess['user_email'] = 'guest.legit@example.com'
        sess['user_role'] = 'guest'

    res = client.post('/api/transactions/TXN_TEST_1/simulate-pay')
    assert res.status_code == 200

# ---------------------------------------------------------
# Part 2: Real-Time Sync Architecture
# ---------------------------------------------------------

def test_sync_hub_channel_scoping():
    """Part 2.1: Pub/sub bus correctly filters events per subscriber channels."""
    sub_kitchen = sync_hub.subscribe(['kitchen'])
    sub_frontdesk = sync_hub.subscribe(['front_desk'])

    sync_hub.publish('kitchen', 'new_order', {'order_no': 'ORD101'})

    # Kitchen gets the event
    assert not sub_kitchen.queue.empty()
    evt = sub_kitchen.queue.get_nowait()
    assert evt['channel'] == 'kitchen'
    assert evt['event'] == 'new_order'
    assert evt['data']['order_no'] == 'ORD101'

    # Frontdesk does NOT get the kitchen event
    assert sub_frontdesk.queue.empty()

    sync_hub.unsubscribe(sub_kitchen)
    sync_hub.unsubscribe(sub_frontdesk)

def test_sync_stream_endpoint(client):
    """Part 2.2: SSE GET /api/sync/stream returns text/event-stream."""
    with client.session_transaction() as sess:
        sess['user_email'] = 'frontdesk@nur-e-haya.com'
        sess['user_role'] = 'front_desk'

    res = client.get('/api/sync/stream?channels=front_desk,announcements')
    assert res.status_code == 200
    assert 'text/event-stream' in res.content_type

# ---------------------------------------------------------
# Part 4: Staff Roles, Hollow Screens & Workflows
# ---------------------------------------------------------

def test_invite_accept_creates_user(client):
    """Part 4.1: POST /api/invite/<token>/accept validates token and activates account."""
    from app.firebase_db import staff_invites_col
    token = "test_valid_invite_token_123"
    staff_invites_col().document(token).set({
        "token": token,
        "email": "new.sommelier@nur-e-haya.com",
        "role": "dining",
        "staff_role": "sommelier",
        "used": False
    })

    res = client.post(f'/api/invite/{token}/accept', json={
        "name": "Arman Laurent",
        "password": "SecurePassword@123"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data.get("ok") is True or data.get("success") is True

    # User doc must now exist in users_col
    u_doc = users_col().document("new.sommelier@nur-e-haya.com").get()
    if not u_doc.exists:
        matches = list(users_col().where('email', '==', 'new.sommelier@nur-e-haya.com').stream())
        assert len(matches) > 0
        u_data = matches[0].to_dict()
    else:
        u_data = u_doc.to_dict()
    assert u_data["name"] == "Arman Laurent"

    # Token must be marked used
    inv_doc = staff_invites_col().document(token).get()
    assert inv_doc.to_dict()["used"] is True

def test_dining_table_status_update(client):
    """Screen 1: PATCH /api/dining/tables/<table_id> persists status changes."""
    restaurant_tables_col().document("tbl_T-05").set({
        "table_no": "T-05",
        "capacity": 4,
        "status": "available"
    })

    with client.session_transaction() as sess:
        sess['user_email'] = 'waiter@nur-e-haya.com'
        sess['user_role'] = 'waiter'

    res = client.patch('/api/dining/tables/tbl_T-05', json={"status": "occupied", "guest_name": "Dr. Sen"})
    assert res.status_code == 200

    updated = restaurant_tables_col().document("tbl_T-05").get()
    assert updated.to_dict()["status"] == "occupied"

def test_events_scheduling_api(client):
    """Screen 2: POST /api/events/calendar schedules a real event."""
    with client.session_transaction() as sess:
        sess['user_email'] = 'events@nur-e-haya.com'
        sess['user_role'] = 'events'

    res = client.post('/api/events/calendar', json={
        "hall_name": "Grand Kohinoor Ballroom",
        "event_type": "Annual Medical Symposium",
        "event_date": "2026-10-15",
        "guest_count": 220,
        "host": "IMA Bengal"
    })
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json.get("ok") is True or res_json.get("success") is True

    # Check that events_calendar renders it
    res_cal = client.get('/events/calendar')
    assert res_cal.status_code == 200
    assert b"Annual Medical Symposium" in res_cal.data

def test_catering_selection_api(client):
    """Screen 4: POST /api/events/catering/select stores selected package."""
    res = client.post('/api/events/catering/select', json={
        "package_name": "Royal Feast Banquet",
        "price_per_plate": 1800
    })
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json.get("ok") is True or res_json.get("success") is True

def test_enquiry_response_api(client):
    """Screen 4: POST /api/events/enquiries/<id>/respond updates quote and status."""
    enq_ref = banquet_bookings_col().add({
        "hall_name": "Sapphire Conference Suite",
        "event_date": "2026-11-01",
        "guest_count": 80,
        "user_email": "client@corporate.org",
        "status": "pending"
    })
    enq_id = enq_ref[1].id

    with client.session_transaction() as sess:
        sess['user_email'] = 'manager@nur-e-haya.com'
        sess['user_role'] = 'manager'

    res = client.post(f'/api/events/enquiries/{enq_id}/respond', json={
        "quote_amount": 95000,
        "notes": "Includes premium AV and afternoon high tea."
    })
    assert res.status_code == 200

    updated = banquet_bookings_col().document(enq_id).get().to_dict()
    assert updated["status"] == "proposal_sent"
    assert updated["quote_amount"] == 95000

def test_loyalty_redeem_api(client):
    """Screen 5: POST /api/crm/loyalty/redeem deducts points and rejects insufficient balance."""
    users_col().document("vip.guest@gmail.com").set({
        "email": "vip.guest@gmail.com",
        "name": "VIP Guest",
        "role": "guest",
        "loyalty_points": 250
    })

    with client.session_transaction() as sess:
        sess['user_email'] = 'vip.guest@gmail.com'
        sess['user_role'] = 'guest'

    # Insufficient points: requires 300, has 250
    res_fail = client.post('/api/crm/loyalty/redeem', json={
        "perk_name": "Gourmet Dinner",
        "points_cost": 300
    })
    assert res_fail.status_code == 400

    # Sufficient points: requires 150, has 250
    res_succ = client.post('/api/crm/loyalty/redeem', json={
        "perk_name": "Airport Limousine",
        "points_cost": 150
    })
    assert res_succ.status_code == 200
    assert res_succ.get_json()["data"]["remaining_points"] == 100

    u = users_col().document("vip.guest@gmail.com").get().to_dict()
    assert u["loyalty_points"] == 100

def test_membership_tier_upgrade(client):
    """Screen 5: POST /api/crm/memberships/tier upgrades user tier and discount."""
    users_col().document("member@club.com").set({
        "email": "member@club.com",
        "name": "Club Member",
        "role": "member",
        "membership_tier": "Silver Traveler",
        "discount_pct": 5
    })

    with client.session_transaction() as sess:
        sess['user_email'] = 'admin@nur-e-haya.com'
        sess['user_role'] = 'admin'

    res = client.post('/api/crm/memberships/tier', json={
        "user_email": "member@club.com",
        "tier": "Presidential Platinum",
        "discount_pct": 15
    })
    assert res.status_code == 200

    u = users_col().document("member@club.com").get().to_dict()
    assert u["membership_tier"] == "Presidential Platinum"
    assert u["discount_pct"] == 15
