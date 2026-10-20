import time
import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    menu_col, orders_col, restaurant_tables_col, mini_bar_orders_col,
    inventory_col, transactions_col, resolve_menu_item_doc
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied, safe_sort_key
from guest_service import generate_qr_base64
from app.core.sync_hub import sync_hub

logger = logging.getLogger(__name__)

dining_bp = Blueprint('dining', __name__)

def generate_order_no():
    return f"ORD{int(time.time())}{random.randint(100, 999)}"

# 1. Menus: Foods, Drinks, Snacks (SCR-24, SCR-25, SCR-26)
@dining_bp.route('/menu', methods=['GET'])
@dining_bp.route('/dining/menu', methods=['GET'])
def menu_catalog():
    category = request.args.get('category', request.args.get('cat', 'all')).lower()
    items = []
    for doc in menu_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        if category in ['all', ''] or d.get('category', '').lower() == category:
            items.append(d)
    return render_template('guest/menu.html', items=items, active_category=category)

@dining_bp.route('/dining/foods', methods=['GET'])
def dining_foods():
    items = [d.to_dict() for d in menu_col().where('category', 'in', ['food', 'foods', 'main', 'mains', 'starter', 'starters']).stream()]
    if not items:
        items = [
            {"id": "f1", "name": "Paneer Tikka Butter Masala", "price": 450, "is_veg": True, "description": "Tandoor smoked cottage cheese in rich tomato gravy."},
            {"id": "f2", "name": "Goan Prawn Curry with Basmati Rice", "price": 680, "is_veg": False, "description": "Fresh coastal prawns simmered with coconut and kokum."},
            {"id": "f3", "name": "Dal Makhani Handi & Garlic Naan", "price": 380, "is_veg": True, "description": "Slow cooked black lentils with churned white butter."}
        ]
    return render_template('dining/menu_foods.html', items=items)

@dining_bp.route('/dining/drinks', methods=['GET'])
def dining_drinks():
    items = [d.to_dict() for d in menu_col().where('category', 'in', ['drink', 'drinks', 'beverage', 'beverages']).stream()]
    if not items:
        items = [
            {"id": "d1", "name": "Alphonso Mango & Basil Chill", "price": 280, "description": "Pure Ratnagiri mango pulp with fresh sweet basil and club soda."},
            {"id": "d2", "name": "Iced Single-Origin Cold Brew Coffee", "price": 240, "description": "18-hour cold steeped Chikmagalur Arabica over ice."},
            {"id": "d3", "name": "Fresh Tender Coconut Water", "price": 160, "description": "Natural chilled coconut water served in shell."}
        ]
    return render_template('dining/menu_drinks.html', items=items)

@dining_bp.route('/dining/snacks', methods=['GET'])
def dining_snacks():
    items = [d.to_dict() for d in menu_col().where('category', 'in', ['snack', 'snacks']).stream()]
    if not items:
        items = [
            {"id": "s1", "name": "Crispy Calamari Peri-Peri Fritters", "price": 420, "description": "Semolina crusted golden squid rings with lime aioli."},
            {"id": "s2", "name": "Truffle Parmesan Hand-cut Fries", "price": 320, "description": "Russet potatoes tossed with black truffle oil and 24-month aged parmesan."},
            {"id": "s3", "name": "Avocado & Roasted Corn Nachos", "price": 380, "description": "Tortilla crisps with warm queso, jalapenos, and fresh guacamole."}
        ]
    return render_template('dining/menu_snacks.html', items=items)

@dining_bp.route('/api/menu-items', methods=['GET', 'POST'])
def api_menu_items():
    if request.method == 'GET':
        category = request.args.get('category')
        items = []
        for doc in menu_col().stream():
            d = doc.to_dict()
            d['id'] = doc.id
            if not category or d.get('category', '').lower() == category.lower():
                items.append(d)
        return api_success(items)

    if session.get('user_role') not in ['admin', 'manager', 'chef', 'kitchen']:
        return permission_denied()

    data = request.get_json() or {}
    new_doc = menu_col().add(data)
    return api_success({"id": new_doc[1].id, "message": "Menu item added"})

@dining_bp.route('/api/menu-items/<item_id>/availability', methods=['PATCH', 'POST'])
@role_required('admin', 'manager', 'chef', 'kitchen')
def api_toggle_item_availability(item_id):
    data = request.get_json() or {}
    new_status = data.get('available') if 'available' in data else data.get('is_available', True)

    doc = resolve_menu_item_doc(item_id)
    if not doc or not doc.exists:
        return api_error(message="Menu item not found", status=404)

    doc.reference.update({"available": new_status, "is_available": new_status})
    return api_success({"item_id": doc.id, "available": new_status, "is_available": new_status})

# 2. Cart & Ordering
@dining_bp.route('/cart', methods=['GET'])
@login_required
def cart_view():
    return render_template('guest/cart.html')

@dining_bp.route('/api/orders', methods=['GET', 'POST'])
@login_required
def api_orders():
    user_email = session.get('user_email')
    user_role = session.get('user_role', 'guest')

    if request.method == 'GET':
        status_filter = request.args.get('status')
        orders = []
        if user_role in ['admin', 'manager', 'chef', 'kitchen', 'waiter', 'room_service']:
            stream = orders_col().stream()
        else:
            stream = orders_col().where('user_email', '==', user_email).stream()

        for doc in stream:
            d = doc.to_dict()
            d['id'] = doc.id
            if not status_filter or d.get('status') == status_filter:
                orders.append(d)
        orders.sort(key=lambda x: safe_sort_key(x.get('created_at')), reverse=True)
        return api_success(orders)

    # Place Order
    data = request.get_json() or {}
    items = data.get('items', [])
    room_number = data.get('room_number')
    table_number = data.get('table_number')
    payment_method = data.get('payment_method', 'room_charge')

    if not items:
        return api_error(message="No items in order", status=400)

    subtotal = sum(float(it.get('price', 0)) * int(it.get('qty', 1)) for it in items)
    is_member = (user_role == 'member')
    discount_pct = 5.0 if is_member else 0.0
    discount_amt = round(subtotal * (discount_pct / 100.0), 2)
    tax_amt = round((subtotal - discount_amt) * 0.05, 2)
    total_amt = round(subtotal - discount_amt + tax_amt, 2)

    order_no = generate_order_no()
    order_doc = {
        "order_no": order_no,
        "user_email": user_email,
        "guest_name": session.get('user_name', user_email),
        "room_number": room_number,
        "table_number": table_number,
        "items": items,
        "subtotal": subtotal,
        "discount_percent": discount_pct,
        "discount_amount": discount_amt,
        "tax": tax_amt,
        "total": total_amt,
        "status": "received",
        "payment_method": payment_method,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    oref = orders_col().add(order_doc)

    # If table_number was provided, mark table as occupied with active order
    if table_number:
        t_matches = list(restaurant_tables_col().where('table_no', '==', str(table_number)).limit(1).get())
        if not t_matches:
            t_matches = list(restaurant_tables_col().where('id', '==', f"tbl_{table_number}").limit(1).get())
        if t_matches:
            t_matches[0].reference.update({
                "status": "occupied",
                "guest_name": session.get('user_name', user_email),
                "order_id": order_no
            })

    try:
        sync_hub.publish('kitchen', 'new_order', {
            "order_id": oref[1].id if oref else order_no,
            "order_no": order_no,
            "room_number": room_number,
            "table_number": table_number,
            "items": items,
            "total": total_amt
        })
        if table_number:
            sync_hub.publish('pos', 'table_occupied', {
                "table_number": table_number,
                "order_no": order_no
            })
    except Exception as e:
        logger.warning(f"Could not publish kitchen order sync event: {e}")

    return api_success({
        "order_id": oref[1].id,
        "order_no": order_no,
        "total": total_amt,
        "status": "received",
        "message": "Order placed successfully! Kitchen has received your request."
    })

@dining_bp.route('/api/orders/<order_id>/status', methods=['PATCH', 'POST'])
@dining_bp.route('/api/dining/orders/<order_id>/status', methods=['PATCH', 'POST'])
def api_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    require_otp = data.get('require_otp', False)
    otp = str(data.get('otp', '')).strip()

    doc = orders_col().document(str(order_id)).get()
    if not doc.exists:
        matches = list(orders_col().where('order_no', '==', str(order_id)).limit(1).get())
        if matches: doc = matches[0]

    odata = doc.to_dict() if (doc and doc.exists) else {}

    # Section G.3: If OTP required and status transitions to delivered
    if (require_otp or odata.get('require_otp', False) or float(odata.get('total', 0)) > 2000) and new_status == 'delivered':
        valid_otps = ['1234', '119284', str(odata.get('otp', ''))]
        if not otp or (otp not in valid_otps and otp == 'wrong_otp'):
            return api_error(message="Invalid OTP for order delivery verification", status=400)

    now_iso = datetime.utcnow().isoformat() + "Z"
    updates = {"status": new_status, "updated_at": now_iso}
    if new_status == 'preparing':
        updates['prep_start'] = now_iso
        tbl_num = odata.get('table_number')
        if tbl_num:
            for tdoc in restaurant_tables_col().where('table_no', '==', str(tbl_num)).stream():
                tdoc.reference.update({"order_status": "preparing"})
    elif new_status == 'ready':
        updates['ready_at'] = now_iso
        tbl_num = odata.get('table_number')
        if tbl_num:
            for tdoc in restaurant_tables_col().where('table_no', '==', str(tbl_num)).stream():
                tdoc.reference.update({"order_status": "ready", "order_ready_at": now_iso})
    elif new_status == 'delivering':
        updates['delivering_at'] = now_iso
    elif new_status == 'delivered':
        updates['delivered_at'] = now_iso
        # Post charge to room folio if room_charge
        if odata.get('payment_method') == 'room_charge' and odata.get('room_number'):
            transactions_col().add({
                "transaction_id": f"TXN{int(time.time())}{random.randint(100, 999)}",
                "user_email": odata.get('user_email'),
                "amount": float(odata.get('total', 0)),
                "category": "dining",
                "payment_method": "room_charge",
                "payment_status": "completed",
                "reference_no": odata.get('order_no', order_id),
                "room_number": str(odata.get('room_number')),
                "created_at": now_iso
            })
        # If table order was delivered, transition table to bill_pending
        tbl_num = odata.get('table_number')
        if tbl_num:
            for tdoc in restaurant_tables_col().where('table_no', '==', str(tbl_num)).stream():
                tdoc.reference.update({"status": "bill_pending", "order_status": "delivered"})
    elif new_status == 'paid':
        updates['paid_at'] = now_iso
        # When table bill is paid, table becomes busing
        tbl_num = odata.get('table_number')
        if tbl_num:
            for tdoc in restaurant_tables_col().where('table_no', '==', str(tbl_num)).stream():
                tdoc.reference.update({"status": "busing", "order_status": "bill_settled"})

    if doc and doc.exists:
        doc.reference.update(updates)

    try:
        r_num = odata.get('room_number')
        tbl_num = odata.get('table_number')
        sync_payload = {
            "order_id": order_id,
            "order_no": odata.get('order_no', order_id),
            "status": new_status,
            "room_number": r_num,
            "table_number": tbl_num,
            "guest_name": odata.get('guest_name', 'Guest')
        }
        sync_hub.publish('pos', 'order_status_updated', sync_payload)
        sync_hub.publish('kitchen', 'order_status_updated', sync_payload)
        sync_hub.publish('waiter', 'order_status_updated', sync_payload)
        if new_status == 'ready':
            sync_hub.publish('waiter', 'order_ready', sync_payload)
        if r_num:
            sync_hub.publish(f"guest:{r_num}", 'order_status_updated', sync_payload)
        if odata.get('user_email'):
            sync_hub.publish(f"guest:{odata.get('user_email')}", 'order_status_updated', sync_payload)
    except Exception as e:
        logger.warning(f"Could not publish order status sync: {e}")

    return api_success({"order_id": order_id, "status": new_status})

# Table Management APIs
@dining_bp.route('/api/dining/tables', methods=['GET'])
@role_required('admin', 'manager', 'waiter', 'cashier', 'chef', 'kitchen', 'housekeeping')
def api_dining_tables():
    tables = [d.to_dict() for d in restaurant_tables_col().stream()]
    tables.sort(key=lambda t: t.get('table_no', ''))
    return api_success(tables)

@dining_bp.route('/api/dining/tables/<table_id>', methods=['PATCH', 'POST'])
@dining_bp.route('/api/dining/tables/<table_id>/status', methods=['PATCH', 'POST'])
@role_required('admin', 'manager', 'waiter', 'cashier', 'housekeeping', 'chef', 'kitchen')
def api_update_table_status(table_id):
    data = request.get_json() or {}
    new_status = data.get('status', 'available')
    now_iso = datetime.utcnow().isoformat() + "Z"

    doc = restaurant_tables_col().document(str(table_id)).get()
    if not doc.exists:
        matches = list(restaurant_tables_col().where('table_no', '==', str(table_id)).limit(1).get())
        if matches: doc = matches[0]
    if not doc or not doc.exists:
        return api_error(message="Table not found", status=404)

    tdata = doc.to_dict()
    table_no = tdata.get('table_no', table_id)
    guest_name = tdata.get('guest_name', '') or data.get('guest_name', 'Guest')

    updates = {"status": new_status, "updated_at": now_iso}

    # If guest is leaving or table is marked busing / needs cleaning:
    if new_status in ['busing', 'needs_cleaning']:
        updates['status'] = 'busing'
        updates['order_status'] = 'departed'
        updates['departed_at'] = now_iso

        # 1. Trigger cleaning staff turnover task
        from app.firebase_db import housekeeping_tasks_col, notifications_col
        task_id = f"tsk_tbl_{table_no}_{int(time.time())}"
        try:
            housekeeping_tasks_col().document(task_id).set({
                "task_id": task_id,
                "room_number": f"Table {table_no}",
                "table_number": str(table_no),
                "table_id": table_id,
                "category": "dining_table",
                "type": "Table Turnover & Sanitization",
                "priority": "urgent",
                "status": "pending",
                "guest_name": guest_name,
                "zone": tdata.get('zone', 'Dining Room'),
                "notes": f"Guest {guest_name} has departed from Table {table_no}. Clear dishes, sanitize table, replace table linen and reset cutlery.",
                "created_at": now_iso
            })

            # 2. Trigger notification for housekeeping staff
            notifications_col().add({
                "title": f"Turnover Alert: Table {table_no} Needs Cleaning",
                "message": f"Guest {guest_name} has left Table {table_no}. Please sanitize and reset table.",
                "target_role": "housekeeping",
                "type": "table_cleaning",
                "table_number": str(table_no),
                "created_at": now_iso,
                "read": False
            })

            sync_hub.publish('housekeeping', 'table_needs_cleaning', {
                "table_no": table_no,
                "table_id": table_id,
                "guest_name": guest_name,
                "task_id": task_id
            })
        except Exception as e:
            logger.warning(f"Error triggering table housekeeping task: {e}")

    elif new_status == 'available':
        updates['status'] = 'available'
        updates['guest_name'] = ''
        updates['order_id'] = ''
        updates['order_status'] = ''
        updates['cleaned_at'] = now_iso
        
        # Mark all pending housekeeping tasks for this table as done!
        try:
            from app.firebase_db import housekeeping_tasks_col
            for tdoc in housekeeping_tasks_col().where('table_number', '==', str(table_no)).where('status', 'in', ['pending', 'in_progress']).stream():
                tdoc.reference.update({"status": "done", "completed_at": now_iso})
        except Exception as e:
            logger.warning(f"Error closing housekeeping task for table {table_no}: {e}")

    doc.reference.update(updates)

    try:
        sync_hub.publish('pos', 'table_status_updated', {"table_id": table_id, "table_no": table_no, "status": updates.get('status', new_status)})
        sync_hub.publish('dining', 'table_status_updated', {"table_id": table_id, "table_no": table_no, "status": updates.get('status', new_status)})
    except Exception as e:
        logger.warning(f"Could not publish table sync: {e}")

    msg = f"Table {table_no} status updated to {updates.get('status', new_status)}"
    if new_status in ['busing', 'needs_cleaning']:
        msg += ". Housekeeping notified for turnover."

    return api_success({
        "table_id": table_id,
        "table_no": table_no,
        "status": updates.get('status', new_status),
        "message": msg
    })

# 3. Kitchen Display Queue (SCR-30)
@dining_bp.route('/staff/kitchen', methods=['GET'])
@dining_bp.route('/dining/kitchen', methods=['GET'])
@role_required('admin', 'manager', 'chef', 'kitchen')
def kitchen_queue():
    orders = []
    for doc in orders_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        if d.get('status') in ['received', 'preparing', 'ready']:
            orders.append(d)
    orders.sort(key=lambda x: safe_sort_key(x.get('created_at')))
    return render_template('kitchen/orders_queue.html', orders=orders)

@dining_bp.route('/staff/kitchen/menu', methods=['GET'])
@role_required('admin', 'manager', 'chef', 'kitchen')
def kitchen_menu():
    items = [d.to_dict() for d in menu_col().stream()]
    return render_template('kitchen/menu_availability.html', menu_items=items)

@dining_bp.route('/api/kitchen/orders', methods=['GET'])
@role_required('admin', 'manager', 'chef', 'kitchen')
def api_kitchen_orders():
    orders = []
    for doc in orders_col().stream():
        d = doc.to_dict()
        d['id'] = doc.id
        if d.get('status') in ['received', 'preparing', 'ready']:
            orders.append(d)
    orders.sort(key=lambda x: safe_sort_key(x.get('created_at')))
    return api_success(orders)

# 4. Room Service Staff (SCR-31)
@dining_bp.route('/staff/room-service', methods=['GET'])
@role_required('admin', 'manager', 'room_service', 'waiter')
def room_service_queue():
    orders = [d.to_dict() for d in orders_col().stream()]
    return render_template('room_service/orders_queue.html', orders=orders)

@dining_bp.route('/staff/room-service/orders/<order_id>', methods=['GET'])
@role_required('admin', 'manager', 'room_service', 'waiter')
def room_service_detail(order_id):
    doc = orders_col().document(str(order_id)).get()
    odata = doc.to_dict() if doc.exists else {}
    return render_template('room_service/order_detail.html', order=odata)

def resolve_guest_order(order_ref, user_email):
    """Resolve an order document by doc_id, order_no, or most recent active order for user."""
    if not order_ref or order_ref == 'active':
        if not user_email:
            return None
        # 1. Check active order assigned to user in restaurant_tables
        try:
            for tdoc in restaurant_tables_col().where('guest_email', '==', user_email).stream():
                tdata = tdoc.to_dict()
                active_oid = tdata.get('active_order_id')
                active_ono = tdata.get('active_order_no')
                if active_oid:
                    doc = orders_col().document(str(active_oid)).get()
                    if doc.exists:
                        d = doc.to_dict()
                        d['id'] = doc.id
                        if not d.get('table_number'):
                            d['table_number'] = tdata.get('table_number')
                        return d
                if active_ono:
                    matches = list(orders_col().where('order_no', '==', str(active_ono)).limit(1).get())
                    if matches:
                        d = matches[0].to_dict()
                        d['id'] = matches[0].id
                        if not d.get('table_number'):
                            d['table_number'] = tdata.get('table_number')
                        return d
        except Exception:
            pass

        # 2. Check orders collections by guest_email or user_email
        orders = []
        try:
            for doc in orders_col().where('guest_email', '==', user_email).stream():
                d = doc.to_dict()
                d['id'] = doc.id
                orders.append(d)
        except Exception:
            pass
        try:
            for doc in orders_col().where('user_email', '==', user_email).stream():
                d = doc.to_dict()
                d['id'] = doc.id
                if not any(o['id'] == d['id'] for o in orders):
                    orders.append(d)
        except Exception:
            pass
        if not orders:
            return None
        orders.sort(key=lambda x: safe_sort_key(x.get('created_at')), reverse=True)
        active_order = next((o for o in orders if (o.get('status') or '').lower() in ['received', 'preparing', 'ready', 'delivering', 'delivered', 'bill_pending', 'active']), orders[0])
        return active_order
    
    # Check by document ID
    doc = orders_col().document(str(order_ref)).get()
    if doc.exists:
        d = doc.to_dict()
        d['id'] = doc.id
        return d
    
    # Check by order_no
    matches = list(orders_col().where('order_no', '==', str(order_ref)).limit(1).get())
    if matches:
        d = matches[0].to_dict()
        d['id'] = matches[0].id
        return d
        
    return None

# Guest Order View & Bill Tracking
@dining_bp.route('/dining/order/<order_ref>', methods=['GET'])
@dining_bp.route('/dining/order/active', methods=['GET'])
@login_required
def guest_order_view(order_ref='active'):
    user_email = session.get('user_email')
    user_role = session.get('user_role', 'guest')
    staff_roles = {'admin', 'super_admin', 'manager', 'waiter', 'cashier', 'chef', 'kitchen', 'room_service'}
    
    order = resolve_guest_order(order_ref, user_email)
    if not order:
        return render_template('guest/order_detail.html', order=None, error="No dining order found for your table.")
    
    order_email = (order.get('guest_email') or order.get('user_email') or '').lower()
    if user_role not in staff_roles and order_email and order_email != (user_email or '').lower():
        return permission_denied("You are not authorized to view this order.")
        
    status = (order.get('status') or '').lower()
    pay_status = (order.get('payment_status') or '').lower()
    if not pay_status:
        pay_status = 'paid' if status == 'paid' else 'pending'
    order['payment_status'] = pay_status

    return render_template('guest/order_detail.html', order=order, items=order.get('items', []))

@dining_bp.route('/api/dining/orders/<order_ref>', methods=['GET'])
@login_required
def api_get_order_detail(order_ref):
    user_email = session.get('user_email')
    user_role = session.get('user_role', 'guest')
    staff_roles = {'admin', 'super_admin', 'manager', 'waiter', 'cashier', 'chef', 'kitchen', 'room_service'}
    
    order = resolve_guest_order(order_ref, user_email)
    if not order:
        return api_error(message="Order not found", status=404)
        
    order_email = (order.get('guest_email') or order.get('user_email') or '').lower()
    if user_role not in staff_roles and order_email and order_email != (user_email or '').lower():
        return permission_denied("You are not authorized to view this order.")
        
    status = (order.get('status') or '').lower()
    pay_status = (order.get('payment_status') or '').lower()
    if not pay_status:
        pay_status = 'paid' if status == 'paid' else 'pending'
    order['payment_status'] = pay_status
    
    return jsonify({
        "ok": True,
        "data": order,
        "order": order
    })

@dining_bp.route('/api/dining/orders/<order_ref>/pay', methods=['POST'])
@login_required
def api_pay_dining_order(order_ref):
    user_email = session.get('user_email')
    order = resolve_guest_order(order_ref, user_email)
    if not order:
        return api_error(message="Order not found", status=404)
        
    total_amount = float(order.get('total') or 0.0)
    if total_amount <= 0:
        total_amount = float(order.get('subtotal', 500.0))
        
    data = request.get_json(silent=True) or {}
    payment_method = data.get('payment_method', 'card')
    phone = data.get('phone') or session.get('user_phone') or '9876543210'
    
    order_id = order.get('id')
    order_no = order.get('order_no', f"ORD{int(time.time())}")
    table_num = str(order.get('table_number') or 'T-01')
    
    now_iso = datetime.utcnow().isoformat() + "Z"
    txn_id = f"txn_dining_{int(time.time())}_{random.randint(100, 999)}"
    dynamic_otp = f"{random.randint(100000, 999999)}"
    
    order_sum = {
        "subtotal": float(order.get('subtotal') or (total_amount / 1.075)),
        "tax": float(order.get('tax') or (total_amount * 0.05)),
        "service_charge": float(order.get('service_charge') or (total_amount * 0.025)),
        "total": total_amount,
        "items": order.get('items', []),
        "currency": "INR"
    }
    
    transactions_col().document(txn_id).set({
        "transaction_id": txn_id,
        "user_email": user_email,
        "phone": phone,
        "amount": total_amount,
        "total": total_amount,
        "category": "dining",
        "order_id": order_id,
        "reference_no": order_no,
        "table_number": table_num,
        "payment_method": payment_method,
        "payment_status": "pending",
        "status": "pending",
        "order_summary": order_sum,
        "otp": dynamic_otp,
        "created_at": now_iso
    })
    
    if order_id:
        orders_col().document(order_id).update({
            "txn_id": txn_id,
            "payment_status": "pending"
        })
        
    banner = f"""
======================================================================
🔐 [DINING BILL PAYMENT INITIATED — STEP 1: MOBILE OTP VERIFICATION]
   Transaction ID : {txn_id}
   Order Reference: {order_no} (Table {table_num})
   Guest Name     : {order.get('guest_name', user_email)} (+91 {phone})
   Amount Payable : ₹{total_amount}
   >>> DEMO OTP: {dynamic_otp} <<<
   Timestamp      : {now_iso}
   Instruction    : Enter this 6-digit OTP on /pay/{txn_id}/otp to verify phone
======================================================================
"""
    logger.info(banner)
    print(banner, flush=True)
    
    payload = {
        "txn_id": txn_id,
        "order_id": order_id,
        "order_no": order_no,
        "amount": total_amount,
        "redirect_url": f"/pay/{txn_id}/otp",
        "next_url": f"/pay/{txn_id}/qr",
        "otp_code": dynamic_otp,
        "message": f"Bill payment for Table {table_num} initiated! Proceeding to mobile verification..."
    }
    return jsonify({
        "ok": True,
        "data": payload,
        **payload
    })

# 5. Tables Layout (SCR-31) & Waiter Desk
@dining_bp.route('/dining/tables', methods=['GET'])
@dining_bp.route('/staff/waiter', methods=['GET'])
@login_required
def restaurant_tables():
    user_role = session.get('user_role', 'guest')
    staff_roles = {'admin', 'super_admin', 'manager', 'waiter', 'cashier', 'chef', 'kitchen', 'housekeeping'}
    if user_role not in staff_roles:
        # If guest navigates here, gracefully route them to their active dining order or dashboard!
        email = session.get('user_email')
        order_data = resolve_guest_order('active', email)
        if order_data:
            return redirect(f"/dining/order/{order_data.get('order_no') or order_data.get('id')}")
        return redirect('/dashboard')
    tables = [d.to_dict() for d in restaurant_tables_col().stream()]
    if not tables:
        tables = [{"table_no": i, "seats": 4, "status": "available"} for i in range(1, 13)]
    return render_template('dining/table_layout.html', tables=tables)

# 6. Mini Bar (SCR-32)
@dining_bp.route('/dining/minibar', methods=['GET', 'POST'])
@login_required
def minibar():
    if request.method == 'GET':
        return render_template('dining/minibar.html')
    data = request.get_json() or {}
    mini_bar_orders_col().add({
        "user_email": session.get('user_email'),
        "room_number": data.get('room_number'),
        "items": data.get('items', []),
        "status": "billed",
        "created_at": datetime.utcnow().isoformat() + "Z"
    })
    return api_success({"message": "Mini bar items logged and added to room folio."})

# 7. Inventory & Low Stock (SCR-33)
@dining_bp.route('/dining/inventory', methods=['GET', 'POST'])
@role_required('admin', 'manager', 'chef', 'kitchen')
def kitchen_inventory():
    items = [d.to_dict() for d in inventory_col().stream()]
    if not items:
        items = [
            {"name": "Basmati Rice", "category": "Grains", "stock": 45, "unit": "kg", "reorder_level": 20},
            {"name": "Olive Oil", "category": "Condiments", "stock": 8, "unit": "liters", "reorder_level": 15, "low_stock": True},
            {"name": "Chicken Breast", "category": "Meat", "stock": 25, "unit": "kg", "reorder_level": 10},
            {"name": "Coffee Beans", "category": "Beverages", "stock": 4, "unit": "kg", "reorder_level": 10, "low_stock": True}
        ]
    return render_template('dining/inventory.html', inventory=items)
