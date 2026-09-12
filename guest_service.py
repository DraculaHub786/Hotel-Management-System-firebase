"""
guest_service.py - Guest module logic, pricing calculation, QR generation, and sample seeds
Fulfills todo.md Section C (Guest Screens C.1 - C.9)
"""

import io
import base64
import random
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Try importing qrcode, provide lightweight SVG fallback if not installed
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

def generate_qr_base64(payload: str) -> str:
    """Generate a base64 encoded PNG of a QR code payload"""
    if HAS_QRCODE:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#104e8b", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.warning(f"qrcode library failed: {str(e)}")
            
    # Fallback to SVG data URI base64 placeholder QR pattern
    dummy_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="220" height="220" viewBox="0 0 220 220">
        <rect width="220" height="220" fill="white" rx="10"/>
        <rect x="20" y="20" width="50" height="50" fill="#162236"/>
        <rect x="30" y="30" width="30" height="30" fill="white"/>
        <rect x="35" y="35" width="20" height="20" fill="#d4af37"/>
        <rect x="150" y="20" width="50" height="50" fill="#162236"/>
        <rect x="160" y="30" width="30" height="30" fill="white"/>
        <rect x="165" y="35" width="20" height="20" fill="#d4af37"/>
        <rect x="20" y="150" width="50" height="50" fill="#162236"/>
        <rect x="30" y="160" width="30" height="30" fill="white"/>
        <rect x="35" y="165" width="20" height="20" fill="#d4af37"/>
        <circle cx="110" cy="110" r="18" fill="#104e8b"/>
        <text x="110" y="115" font-size="10" text-anchor="middle" fill="white" font-weight="bold">SCAN</text>
    </svg>"""
    return base64.b64encode(dummy_svg.encode('utf-8')).decode('utf-8')

def calculate_order_pricing(items, db, is_member=False):
    """
    Recalculates all prices from the database per Section C.5 (never trusts client prices)
    """
    subtotal = 0.0
    detailed_items = []

    rooms_col = db.collection('rooms')
    facilities_col = db.collection('facilities')
    menu_col = db.collection('menu_items')

    for itm in items:
        item_type = itm.get('type')
        ref_id = itm.get('ref_id')
        qty = int(itm.get('qty', 1))

        if item_type == 'room':
            doc = rooms_col.document(str(ref_id)).get()
            if not doc.exists:
                # search by number or id
                matches = list(rooms_col.where('number', '==', str(ref_id)).limit(1).get())
                doc = matches[0] if matches else None
            
            price_per_night = 3500.0
            name = f"Room {ref_id}"
            image = "/static/images/room-deluxe.jpg"
            if doc and doc.exists:
                d = doc.to_dict()
                price_per_night = float(d.get('price') or d.get('price_per_night', 3500))
                name = f"{d.get('type', 'Deluxe')} Room {d.get('number', ref_id)}"
                image = d.get('image', image)
            
            # calculate nights if check_in and check_out provided
            nights = 1
            if itm.get('check_in') and itm.get('check_out'):
                try:
                    ci = datetime.fromisoformat(itm['check_in'].replace('Z', ''))
                    co = datetime.fromisoformat(itm['check_out'].replace('Z', ''))
                    nights = max(1, (co - ci).days)
                except Exception:
                    nights = 1
            
            line_total = price_per_night * nights
            subtotal += line_total
            detailed_items.append({
                "type": "room",
                "ref_id": ref_id,
                "name": name,
                "nights": nights,
                "unit_price": price_per_night,
                "line_total": line_total,
                "check_in": itm.get('check_in'),
                "check_out": itm.get('check_out'),
                "image": image
            })

        elif item_type == 'facility':
            doc = facilities_col.document(str(ref_id)).get()
            price = 1500.0
            name = f"Facility {ref_id}"
            if doc and doc.exists:
                d = doc.to_dict()
                price = float(d.get('price', 1500))
                name = d.get('name', name)
            
            subtotal += price
            detailed_items.append({
                "type": "facility",
                "ref_id": ref_id,
                "name": name,
                "slot": itm.get('slot', 'Standard Slot'),
                "date": itm.get('date', datetime.utcnow().strftime('%Y-%m-%d')),
                "unit_price": price,
                "line_total": price
            })

        elif item_type == 'menu':
            doc = menu_col.document(str(ref_id)).get()
            price = 450.0
            name = f"Menu Item {ref_id}"
            if doc and doc.exists:
                d = doc.to_dict()
                price = float(d.get('price', 450))
                name = d.get('name', name)
            
            line_total = price * qty
            subtotal += line_total
            detailed_items.append({
                "type": "menu",
                "ref_id": ref_id,
                "name": name,
                "qty": qty,
                "unit_price": price,
                "line_total": line_total
            })

    # Member discount 5%
    discount_amount = (subtotal * 0.05) if is_member else 0.0
    taxable_amount = max(0.0, subtotal - discount_amount)
    
    # 5% GST tax, 2.5% service charge per Section C.5 spec
    tax = round(taxable_amount * 0.05, 2)
    service_charge = round(taxable_amount * 0.025, 2)
    total = round(taxable_amount + tax + service_charge, 2)

    return {
        "subtotal": round(subtotal, 2),
        "discount": round(discount_amount, 2),
        "tax": tax,
        "service_charge": service_charge,
        "total": total,
        "currency": "INR",
        "items": detailed_items
    }

def init_sample_facilities_and_menu(db):
    """Seed facilities and menu items if collection is empty"""
    try:
        fac_col = db.collection('facilities')
        if not list(fac_col.limit(1).get()):
            sample_facilities = [
                {
                    "id": "fac_spa",
                    "name": "Nur-e-Sultana Luxury Spa",
                    "category": "wellness",
                    "price": 3200,
                    "duration": "90 mins",
                    "capacity": 8,
                    "description": "Indulge in holistic therapies, Moroccan bath, and authentic aromatherapy massages.",
                    "slots": ["10:00 AM", "12:00 PM", "02:30 PM", "04:30 PM", "07:00 PM"],
                    "image": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=600&q=80"
                },
                {
                    "id": "fac_pool",
                    "name": "Rooftop Infinity Heated Pool",
                    "category": "recreation",
                    "price": 1200,
                    "duration": "120 mins",
                    "capacity": 20,
                    "description": "Panoramic city skyline view with private cabanas and refreshing beverages.",
                    "slots": ["07:00 AM", "09:30 AM", "03:00 PM", "05:30 PM", "08:00 PM"],
                    "image": "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=600&q=80"
                },
                {
                    "id": "fac_gym",
                    "name": "State-of-the-Art Fitness Arena",
                    "category": "fitness",
                    "price": 800,
                    "duration": "60 mins",
                    "capacity": 15,
                    "description": "Technogym equipment, personal trainers on request, steam room and sauna access.",
                    "slots": ["06:00 AM", "08:00 AM", "10:00 AM", "05:00 PM", "07:00 PM"],
                    "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=600&q=80"
                }
            ]
            for f in sample_facilities:
                fac_col.document(f['id']).set(f)
            logger.info("🌱 Facilities seeded")

        menu_col = db.collection('menu_items')
        if not list(menu_col.limit(1).get()):
            sample_menu = [
                {
                    "id": "item_12",
                    "name": "Royal Club Sandwich",
                    "category": "food",
                    "price": 450,
                    "available": True,
                    "diet": "non-veg",
                    "prep_time": "15 mins",
                    "description": "Triple-decker smoked chicken, fried egg, aged cheddar, crisp lettuce with truffle fries.",
                    "image": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80"
                },
                {
                    "id": "item_13",
                    "name": "Dal Makhani & Butter Naan",
                    "category": "food",
                    "price": 550,
                    "available": True,
                    "diet": "veg",
                    "prep_time": "20 mins",
                    "description": "Slow cooked black lentils with white butter, served with clay oven baked garlic naan.",
                    "image": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=600&q=80"
                },
                {
                    "id": "item_14",
                    "name": "Grilled Salmon Steak",
                    "category": "food",
                    "price": 950,
                    "available": True,
                    "diet": "non-veg",
                    "prep_time": "25 mins",
                    "description": "Atlantic salmon, asparagus spears, saffron lemon butter glaze, mashed potatoes.",
                    "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=600&q=80"
                },
                {
                    "id": "item_15",
                    "name": "Kashmiri Kahwa & Baklava",
                    "category": "drink",
                    "price": 320,
                    "available": True,
                    "diet": "veg",
                    "prep_time": "10 mins",
                    "description": "Aromatic green tea infused with saffron, cardamom, and sliced almonds with pistachio baklava.",
                    "image": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80"
                }
            ]
            for m in sample_menu:
                menu_col.document(m['id']).set(m)
            logger.info("🌱 Menu items seeded")
    except Exception as e:
        logger.warning(f"Error seeding facilities/menu: {str(e)}")
