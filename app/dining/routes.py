import time
import random
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.firebase_db import (
    menu_col, orders_col, restaurant_tables_col, mini_bar_orders_col,
    inventory_col, transactions_col
)
from app.auth.decorators import login_required, role_required
from api_utils import api_success, api_error, permission_denied
from guest_service import generate_qr_base64

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
    new_status = data.get('available', True)

    doc = menu_col().document(str(item_id)).get()
    if not doc.exists:
        # Search by id field
        matches = list(menu_col().where('id', '==', str(item_id)).limit(1).get())
        if matches: doc = matches[0]

    if not doc or not doc.exists:
        return api_error(message="Menu item not found", status=404)

    doc.reference.update({"available": new_status})
    return api_success({"item_id": item_id, "available": new_status})

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
        orders.sort(key=lambda x: x.get('created_at', ''), reverse=True)
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

    return api_success({
        "order_id": oref[1].id,
        "order_no": order_no,
        "total": total_amt,
        "status": "received",
        "message": "Order placed successfully! Kitchen has received your request."
    })

@dining_bp.route('/api/orders/<order_id>/status', methods=['PATCH', 'POST'])
def api_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get('status')
    require_otp = data.get('require_otp', False)
    otp = data.get('otp', '')

    if require_otp and new_status == 'delivered' and otp != '1234':
        return api_error(message="Invalid OTP for order delivery verification", status=400)

    doc = orders_col().document(str(order_id)).get()
    if not doc.exists:
        matches = list(orders_col().where('order_no', '==', str(order_id)).limit(1).get())
        if matches: doc = matches[0]

    updates = {"status": new_status, "updated_at": datetime.utcnow().isoformat() + "Z"}
    if new_status == 'preparing':
        updates['prep_start'] = datetime.utcnow().isoformat() + "Z"
    elif new_status == 'ready':
        updates['ready_at'] = datetime.utcnow().isoformat() + "Z"
    elif new_status == 'paid':
        updates['paid_at'] = datetime.utcnow().isoformat() + "Z"

    if doc and doc.exists:
        doc.reference.update(updates)
    return api_success({"order_id": order_id, "status": new_status})

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
    orders.sort(key=lambda x: x.get('created_at', ''))
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

# 5. Tables Layout (SCR-31)
@dining_bp.route('/dining/tables', methods=['GET'])
@role_required('admin', 'manager', 'waiter', 'cashier', 'chef', 'kitchen')
def restaurant_tables():
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
