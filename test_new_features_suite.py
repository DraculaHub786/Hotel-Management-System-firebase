import os
import json
import pytest
from datetime import datetime
from app import create_app
from app.firebase_db import (
    users_col, bookings_col, orders_col, transactions_col,
    restaurant_tables_col, housekeeping_tasks_col, notifications_col
)

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client

def test_google_auto_registration_and_direct_login(client):
    """Test that a brand new Google user is directly registered and logged in without prior signup."""
    new_user_email = f"google_test_guest_{int(datetime.utcnow().timestamp())}@example.com"
    new_user_name = "Google Traveler"
    
    # 1. Post to /api/google-auth with dev/demo token
    resp = client.post('/api/google-auth', json={
        'credential': f"demo_token_{new_user_email}",
        'email': new_user_email,
        'name': new_user_name,
        'picture': 'https://lh3.googleusercontent.com/a/test-avatar'
    })
    
    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data.get('ok') is True
    data = res_data.get('data', {})
    assert data['user']['email'] == new_user_email
    assert data['user']['name'] == new_user_name
    assert data['user']['role'] == 'guest'
    assert 'redirect_url' in data

    # Verify session is established
    with client.session_transaction() as sess:
        assert sess.get('user_email') == new_user_email
        assert sess.get('user_role') == 'guest'
        assert sess.get('auth_provider') == 'google'

    # Verify user exists in Firestore
    user_doc = users_col().document(new_user_email).get()
    assert user_doc.exists
    u_data = user_doc.to_dict()
    assert u_data['email'] == new_user_email
    assert u_data['name'] == new_user_name
    assert u_data['role'] == 'guest'
    assert u_data.get('google_auth') is True
    assert u_data.get('loyalty_points') == 25

def test_account_profile_update(client):
    """Test updating all profile settings: username, phone, age, dietary pref, address."""
    user_email = f"profile_update_user_{int(datetime.utcnow().timestamp())}@example.com"
    
    # Create baseline user
    users_col().document(user_email).set({
        'name': 'Original Name',
        'email': user_email,
        'role': 'guest',
        'created_at': datetime.utcnow().isoformat() + "Z"
    })
    
    # Authenticate session
    with client.session_transaction() as sess:
        sess['user_email'] = user_email
        sess['user_name'] = 'Original Name'
        sess['user_role'] = 'guest'
        
    # Update profile
    update_payload = {
        'name': 'Updated Luxury Guest',
        'username': 'luxury_guest_99',
        'phone': '+1987654321',
        'secondary_email': 'luxury.backup@example.com',
        'age': '32',
        'gender': 'Female',
        'nationality': 'Swiss',
        'id_type': 'Passport',
        'id_number': 'P12345678',
        'address': 'Grand Alpine Vista 42',
        'city': 'Geneva',
        'state': 'Geneva',
        'country': 'Switzerland',
        'pincode': '1201',
        'dietary_preference': 'Vegetarian',
        'stay_preferences': 'High floor, quiet wing, extra pillows',
        'emergency_contact_name': 'Hans Swiss',
        'emergency_contact_phone': '+41791234567',
        'emergency_contact_relation': 'Spouse'
    }
    
    resp = client.post('/api/user/profile', json=update_payload)
    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data.get('ok') is True
    assert res_data.get('data', {}).get('user', {}).get('name') == 'Updated Luxury Guest'
    
    # Check session updated
    with client.session_transaction() as sess:
        assert sess.get('user_name') == 'Updated Luxury Guest'
        
    # Check Firestore
    u_doc = users_col().document(user_email).get().to_dict()
    assert u_doc['name'] == 'Updated Luxury Guest'
    assert u_doc['phone'] == '+1987654321'
    assert u_doc['secondary_email'] == 'luxury.backup@example.com'
    assert u_doc['age'] == '32' or u_doc['age'] == 32
    assert u_doc['dietary_preference'] == 'Vegetarian'
    assert u_doc['emergency_contact_name'] == 'Hans Swiss'

def test_active_stay_and_dining_api(client):
    """Test active room badge and active table badge detection for guest."""
    guest_email = f"active_stay_guest_{int(datetime.utcnow().timestamp())}@example.com"
    
    # Create booking with status confirmed and payment completed
    booking_id = f"test_bk_{int(datetime.utcnow().timestamp())}"
    bookings_col().document(booking_id).set({
        'user_email': guest_email,
        'guest_email': guest_email,
        'room_number': 'Royal-301',
        'status': 'confirmed',
        'payment_status': 'completed',
        'check_in': datetime.utcnow().strftime('%Y-%m-%d'),
        'check_out': '2026-12-31',
        'created_at': datetime.utcnow().isoformat() + "Z"
    })
    
    # Create active dining order
    order_id = f"test_ord_{int(datetime.utcnow().timestamp())}"
    orders_col().document(order_id).set({
        'user_email': guest_email,
        'table_number': 'T-08',
        'status': 'preparing',
        'created_at': datetime.utcnow().isoformat() + "Z"
    })
    
    # Set session
    with client.session_transaction() as sess:
        sess['user_email'] = guest_email
        sess['user_role'] = 'guest'
        sess['user_name'] = 'Active Guest'
        
    resp = client.get('/api/user/active-stay-dining')
    assert resp.status_code == 200
    res_data = resp.get_json()
    assert res_data.get('ok') is True
    data = res_data.get('data', {})
    assert data.get('has_active_stay') is True
    assert data.get('active_room', {}).get('room_number') == 'Royal-301'
    assert data.get('has_active_dining') is True
    assert data.get('active_dining', {}).get('table_number') == 'T-08'
    assert data.get('active_dining', {}).get('status') == 'preparing'

def test_full_dining_workflow_cook_waiter_cleaning(client):
    """
    Test End-to-End Restaurant Flow:
    1. Waiter/Kitchen manages table T-99 & order.
    2. Cook marks order status -> 'ready' (Cooked & Ready for Waiter).
    3. Waiter sets table status -> 'occupied' (Food Delivered).
    4. Waiter sets table status -> 'busing' (Guest Leaving / Clean Table).
       - Automatically generates a housekeeping task with priority 'urgent' and notification.
    5. Cleaning staff updates housekeeping task -> 'done'.
       - Linked table status automatically reverts to 'available'!
    """
    table_id = f"tbl_test_{int(datetime.utcnow().timestamp())}"
    table_num = f"T-99-{int(datetime.utcnow().timestamp()) % 1000}"
    
    restaurant_tables_col().document(table_id).set({
        'table_number': table_num,
        'table_no': table_num,
        'table_name': f"Terrace Table {table_num}",
        'status': 'occupied',
        'assigned_guest_name': 'Lord Sterling',
        'guest_name': 'Lord Sterling',
        'assigned_guest_email': 'sterling@example.com',
        'capacity': 4
    })
    
    order_id = f"ord_test_{int(datetime.utcnow().timestamp())}"
    orders_col().document(order_id).set({
        'table_number': table_num,
        'table_id': table_id,
        'user_email': 'sterling@example.com',
        'guest_name': 'Lord Sterling',
        'items': [{'name': 'Wagyu Ribeye', 'quantity': 1, 'price': 85}],
        'status': 'preparing',
        'created_at': datetime.utcnow().isoformat() + "Z"
    })
    
    # Step 1: Cook advances order to 'ready'
    with client.session_transaction() as sess:
        sess['user_email'] = 'chef.marco@example.com'
        sess['user_role'] = 'cook'
        sess['user_name'] = 'Chef Marco'
        
    resp_cook = client.post(f'/api/dining/orders/{order_id}/status', json={'status': 'ready'})
    assert resp_cook.status_code == 200
    cook_res = resp_cook.get_json()
    assert cook_res.get('ok') is True
    
    # Check order is ready
    ord_doc = orders_col().document(order_id).get().to_dict()
    assert ord_doc['status'] == 'ready'
    assert 'ready_at' in ord_doc
    
    # Step 2: Waiter marks food delivered (table status 'occupied')
    with client.session_transaction() as sess:
        sess['user_email'] = 'waiter.elena@example.com'
        sess['user_role'] = 'waiter'
        sess['user_name'] = 'Elena Waiter'
        
    resp_waiter_deliv = client.post(f'/api/dining/tables/{table_id}/status', json={'status': 'occupied'})
    assert resp_waiter_deliv.status_code == 200
    deliv_res = resp_waiter_deliv.get_json()
    assert deliv_res.get('ok') is True
    
    # Step 3: Guest is leaving -> Waiter marks table as 'busing'
    resp_busing = client.post(f'/api/dining/tables/{table_id}/status', json={'status': 'busing'})
    assert resp_busing.status_code == 200
    busing_data = resp_busing.get_json()
    assert busing_data.get('ok') is True
    assert 'Housekeeping notified' in busing_data.get('data', {}).get('message', '')
    
    # Verify Housekeeping task was created
    hk_tasks = list(housekeeping_tasks_col().where('table_id', '==', table_id).stream())
    assert len(hk_tasks) > 0
    task_doc = hk_tasks[0]
    task_data = task_doc.to_dict()
    assert task_data['priority'] == 'urgent'
    assert task_data['type'] == 'Table Turnover & Sanitization'
    assert task_data['table_number'] == table_num
    assert task_data['status'] == 'pending'
    task_id = task_doc.id
    
    # Step 4: Cleaning staff marks task done
    with client.session_transaction() as sess:
        sess['user_email'] = 'housekeeping.staff@example.com'
        sess['user_role'] = 'housekeeping'
        sess['user_name'] = 'Cleaner Sarah'
        
    resp_hk_done = client.put(f'/api/housekeeping/tasks/{task_id}', json={'status': 'done'})
    assert resp_hk_done.status_code == 200
    hk_res = resp_hk_done.get_json()
    assert hk_res.get('ok') is True
    
    # Verify Table status was automatically reset to 'available'!
    table_doc = restaurant_tables_col().document(table_id).get().to_dict()
    assert table_doc['status'] == 'available'
    assert table_doc.get('assigned_guest_name') == '' or table_doc.get('assigned_guest_name') is None

def test_kitchen_queue_sorting_with_mixed_datetime_types(client):
    """
    Test that /dining/kitchen and /staff/kitchen sort seamlessly when orders collection
    contains a mix of datetime objects and ISO strings without raising TypeError.
    """
    ts = int(datetime.utcnow().timestamp())
    # Order 1 with python datetime object
    orders_col().document(f"ord_mix_dt_{ts}").set({
        'table_number': 'T-01',
        'status': 'preparing',
        'created_at': datetime.utcnow(),
        'items': [{'name': 'Paneer Tikka', 'quantity': 1}]
    })
    # Order 2 with string ISO date
    orders_col().document(f"ord_mix_str_{ts}").set({
        'table_number': 'T-02',
        'status': 'received',
        'created_at': datetime.utcnow().isoformat() + "Z",
        'items': [{'name': 'Dal Makhani', 'quantity': 1}]
    })
    
    with client.session_transaction() as sess:
        sess['user_email'] = 'head_chef@example.com'
        sess['user_role'] = 'chef'
        sess['user_name'] = 'Head Chef Gordon'

    resp = client.get('/dining/kitchen')
    assert resp.status_code == 200
    assert b"Kitchen" in resp.data or b"Queue" in resp.data

def test_all_staff_portals_rendering(client):
    """
    Test that Waiter, Concierge, Housekeeping, and Kitchen screens render without template syntax errors or exceptions.
    """
    # 1. Waiter screen
    with client.session_transaction() as sess:
        sess['user_email'] = 'waiter.test@example.com'
        sess['user_role'] = 'waiter'
        sess['user_name'] = 'Waiter Test'
    resp_waiter = client.get('/staff/waiter')
    assert resp_waiter.status_code == 200
    assert b"Dining Room Layout" in resp_waiter.data or b"Tables" in resp_waiter.data

    resp_tables = client.get('/dining/tables')
    assert resp_tables.status_code == 200

    # 2. Concierge screen
    with client.session_transaction() as sess:
        sess['user_email'] = 'concierge.test@example.com'
        sess['user_role'] = 'concierge'
        sess['user_name'] = 'Concierge Test'
    resp_concierge = client.get('/staff/concierge')
    assert resp_concierge.status_code == 200

    resp_queue = client.get('/concierge/queue')
    assert resp_queue.status_code == 200

    # 3. Housekeeping screen
    with client.session_transaction() as sess:
        sess['user_email'] = 'housekeeping.test@example.com'
        sess['user_role'] = 'housekeeping'
        sess['user_name'] = 'Housekeeper Test'
    resp_hk = client.get('/staff/housekeeping')
    assert resp_hk.status_code == 200
    assert b"Housekeeping: Task Board" in resp_hk.data or b"Task Board" in resp_hk.data

    # 4. Kitchen / Chef screen
    with client.session_transaction() as sess:
        sess['user_email'] = 'chef.test@example.com'
        sess['user_role'] = 'chef'
        sess['user_name'] = 'Chef Test'
    resp_kitchen = client.get('/staff/kitchen')
    assert resp_kitchen.status_code == 200
    assert b"Kitchen Display System" in resp_kitchen.data

def test_create_booking_modern_payment_flow_e2e(client):
    """
    Test End-to-End Room Booking Creation & Modern Payment Flow:
    1. Verify /api/rooms & /api/rooms/available return rooms catalog.
    2. POST /api/bookings creates booking & pending transaction with dynamic OTP.
    3. Verify redirect_url is /pay/<txn_id>/otp.
    4. Verify OTP via /api/otp/verify.
    5. Complete payment simulation via /api/transactions/<txn_id>/simulate-pay.
    6. Verify booking becomes confirmed & paid.
    7. Verify /api/user/active-stay-dining reflects the newly booked room.
    """
    guest_email = f"booker_{int(datetime.utcnow().timestamp())}@example.com"
    with client.session_transaction() as sess:
        sess['user_email'] = guest_email
        sess['user_role'] = 'guest'
        sess['user_name'] = 'VIP Booker'
        sess['user_phone'] = '9876543210'

    # 1. Check rooms catalog
    r_resp = client.get('/api/rooms')
    assert r_resp.status_code == 200
    r_data = r_resp.get_json()
    assert r_data.get('ok') is True
    assert len(r_data.get('data', [])) > 5, "Hotel catalog should return all rooms, not just 5"

    # 2. Initiate Booking
    booking_payload = {
        "room_number": "204",
        "room_type": "Heritage Suite",
        "check_in": "2026-11-01",
        "check_out": "2026-11-03",
        "guests": 2,
        "total_price": 7000.0,
        "special_requests": "Quiet room near the royal garden",
        "billing_name": "VIP Booker",
        "phone": "9876543210",
        "payment_method": "card"
    }

    b_resp = client.post('/api/bookings', json=booking_payload)
    assert b_resp.status_code == 200
    b_data = b_resp.get_json()
    assert b_data.get('ok') is True
    data = b_data.get('data', {})
    txn_id = data.get('txn_id')
    booking_id = data.get('booking_id')
    otp_code = data.get('otp_code')
    redirect_url = data.get('redirect_url')

    assert txn_id is not None
    assert booking_id is not None
    assert otp_code is not None and len(otp_code) == 6
    assert redirect_url == f"/pay/{txn_id}/otp"

    # 3. Check transaction stored in Firestore
    tdoc = transactions_col().document(txn_id).get()
    assert tdoc.exists
    tdata = tdoc.to_dict()
    assert tdata.get('status') == 'pending'
    assert tdata.get('otp') == otp_code
    assert float(tdata.get('amount')) == 7000.0

    # 4. Verify OTP on /api/otp/verify
    otp_resp = client.post('/api/otp/verify', json={
        "txn_id": txn_id,
        "otp": otp_code
    })
    assert otp_resp.status_code == 200
    otp_data = otp_resp.get_json()
    assert otp_data.get('ok') is True
    assert f"/pay/{txn_id}" in otp_data.get('data', {}).get('next_url')

    # 5. Simulate payment on /api/transactions/<txn_id>/simulate-pay
    pay_resp = client.post(f"/api/transactions/{txn_id}/simulate-pay")
    assert pay_resp.status_code == 200
    pay_data = pay_resp.get_json()
    assert pay_data.get('ok') is True
    assert pay_data.get('data', {}).get('status') == 'paid'

    # 6. Verify booking updated to confirmed & paid in Firestore
    b_doc = bookings_col().document(booking_id).get()
    assert b_doc.exists
    b_record = b_doc.to_dict()
    assert b_record.get('status') == 'confirmed'
    assert b_record.get('payment_status') == 'paid'

    # 7. Verify active stay endpoint shows this room
    stay_resp = client.get('/api/user/active-stay-dining')
    assert stay_resp.status_code == 200
    stay_data = stay_resp.get_json()
    assert stay_data.get('ok') is True
    stay_info = stay_data.get('data', {})
    assert stay_info.get('has_active_stay') is True
    assert stay_info.get('active_room', {}).get('room_number') == '204'


def test_guest_view_and_pay_dining_order_e2e(client):
    """
    Test guest dining order view, avoiding 403 access denied when accessing /dining/tables,
    fetching live order details, initiating payment, verifying OTP, and settling bill.
    """
    guest_email = f"dining_guest_{int(datetime.utcnow().timestamp())}@example.com"
    order_no = f"ORD{int(datetime.utcnow().timestamp())}"
    table_num = "T-02"

    # Setup order in Firestore
    order_data = {
        'order_no': order_no,
        'guest_email': guest_email,
        'guest_name': "Dining Gourmet",
        'table_number': table_num,
        'status': 'delivered',
        'payment_status': 'pending',
        'items': [
            {'name': 'Shahi Paneer Tikka', 'quantity': 2, 'unit_price': 450.0},
            {'name': 'Garlic Naan Basket', 'quantity': 3, 'unit_price': 120.0}
        ],
        'subtotal': 1260.0,
        'tax': 94.5,
        'total': 1354.5,
        'created_at': datetime.utcnow().isoformat()
    }
    order_ref = orders_col().add(order_data)[1]

    # Setup table in Firestore
    tbl_id = f"tbl_{table_num}"
    restaurant_tables_col().document(tbl_id).set({
        'table_number': table_num,
        'status': 'occupied',
        'active_order_id': order_ref.id,
        'active_order_no': order_no,
        'guest_email': guest_email,
        'order_status': 'delivered'
    }, merge=True)

    with client.session_transaction() as sess:
        sess['user_email'] = guest_email
        sess['user_role'] = 'guest'
        sess['user_name'] = 'Dining Gourmet'

    # 1. Guest visits /dining/tables -> Must gracefully redirect to /dining/order/<order_no> instead of 403 Access Denied
    resp_tbl = client.get('/dining/tables')
    assert resp_tbl.status_code in [302, 301]
    assert f"/dining/order/{order_no}" in resp_tbl.location or "/dining/order" in resp_tbl.location

    # 2. Guest visits /dining/order/active or /dining/order/<order_no>
    resp_page = client.get(f"/dining/order/{order_no}")
    assert resp_page.status_code == 200
    assert b"Shahi Paneer Tikka" in resp_page.data
    assert b"PAYMENT PENDING" in resp_page.data
    assert b"1,354.50" in resp_page.data or b"1354.5" in resp_page.data

    # 3. Guest calls API /api/dining/orders/<order_no>
    resp_api = client.get(f"/api/dining/orders/{order_no}")
    assert resp_api.status_code == 200
    order_json = resp_api.get_json()
    assert order_json.get('ok') is True
    assert order_json['order']['table_number'] == table_num
    assert order_json['order']['payment_status'] == 'pending'

    # 4. Guest calls /api/dining/orders/<order_no>/pay to start modern payment flow
    pay_init = client.post(f"/api/dining/orders/{order_no}/pay", json={})
    assert pay_init.status_code == 200
    pdata = pay_init.get_json()
    assert pdata.get('ok') is True
    txn_id = pdata.get('txn_id')
    assert txn_id is not None
    assert f"/pay/{txn_id}/otp" in pdata.get('redirect_url')

    # Get generated OTP from transaction doc
    tdoc = transactions_col().document(txn_id).get()
    assert tdoc.exists
    tinfo = tdoc.to_dict()
    otp_code = tinfo.get('otp')
    assert otp_code is not None

    # 5. Verify OTP
    otp_resp = client.post('/api/otp/verify', json={
        'txn_id': txn_id,
        'otp': otp_code
    })
    assert otp_resp.status_code == 200
    assert otp_resp.get_json().get('ok') is True

    # 6. Simulate payment completion
    sim_resp = client.post(f"/api/transactions/{txn_id}/simulate-pay")
    assert sim_resp.status_code == 200
    sim_json = sim_resp.get_json()
    assert sim_json.get('ok') is True
    assert sim_json.get('data', {}).get('status') == 'paid'

    # 7. Verify order updated to paid in Firestore
    updated_order = orders_col().document(order_ref.id).get().to_dict()
    assert updated_order.get('payment_status') == 'paid'
    assert updated_order.get('status') == 'paid'

    # 8. Reload guest order page -> shows PAID
    resp_paid_page = client.get(f"/dining/order/{order_no}")
    assert resp_paid_page.status_code == 200
    assert b"BILL PAID IN FULL" in resp_paid_page.data or b"PAID" in resp_paid_page.data



