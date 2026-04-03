# app.py - Main Flask Application  Firebase connection ke saath!
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime, timedelta
from chatbot import get_bot_response, chatbot_instance
import os
import secrets
from functools import wraps
import re
import time
import random
import json
from dotenv import load_dotenv
import bcrypt
import logging

# Load environment variables
load_dotenv()

import firebase_admin
from firebase_admin import credentials, firestore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Use environment variable for secret key - MUST be set in production
secret_key = os.getenv('SECRET_KEY')
if not secret_key:
    if os.getenv('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY environment variable must be set in production!")
    secret_key = secrets.token_hex(32)
    logger.warning("Using generated SECRET_KEY - sessions will be lost on restart!")

app.secret_key = secret_key

# Session security configuration
app.config.update(
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
)

CORS(app)

# Load Firebase credentials from environment variable
firebase_creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
if not os.path.exists(firebase_creds_path):
    logger.error(f"Firebase credentials file not found: {firebase_creds_path}")
    raise FileNotFoundError(f"Firebase credentials file not found at {firebase_creds_path}")

try:
    cred = credentials.Certificate(firebase_creds_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger.info("✅ Firebase initialized successfully")
except Exception as e:
    logger.error(f"❌ Firebase initialization failed: {str(e)}")
    raise

users_collection = db.collection('users')
rooms_collection = db.collection('rooms')
bookings_collection = db.collection('bookings')
transactions_collection = db.collection('transactions') 
logs_collection = db.collection('logs')



def init_sample_rooms():
    """Initialize sample rooms if empty"""
    rooms = rooms_collection.limit(1).get()
    if not list(rooms):
        sample_rooms = [
            {
                "id": "1", 
                "number": "101", 
                "type": "Single", 
                "price": 2500, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Room Service"],
                "max_guests": 1
            },
            {
                "id": "2", 
                "number": "102", 
                "type": "Suite", 
                "price": 5000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Living Area", "Room Service"],
                "max_guests": 3
            },
            {
                "id": "3", 
                "number": "103", 
                "type": "Luxury", 
                "price": 8000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Jacuzzi", "Ocean View", "Butler Service"],
                "max_guests": 4
            },
            {
                "id": "4", 
                "number": "104", 
                "type": "Double", 
                "price": 4000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Mini Bar", "Room Service"],
                "max_guests": 2
            },
            {
                "id": "5", 
                "number": "105", 
                "type": "Family", 
                "price": 2000, 
                "status": "available", 
                "amenities": ["WiFi", "TV", "AC", "Dining", "Room Service"],
                "max_guests": 4
            }
        ]
        for room in sample_rooms:
            rooms_collection.document(room['id']).set(room)
        print("✅ Sample rooms initialized")



def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt rounds"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def is_valid_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_lower and has_digit

def update_expired_bookings(email: str = None):
    """Update status of expired bookings to 'completed'"""
    try:
        now = datetime.now().isoformat()
        
        # Get all bookings that need status update
        if email:
            bookings = bookings_collection.where('user_email', '==', email).stream()
        else:
            bookings = bookings_collection.stream()
        
        updated_count = 0
        for booking in bookings:
            booking_data = booking.to_dict()
            
            # Only update if status is 'confirmed' (not cancelled or already completed)
            if booking_data.get('status') == 'confirmed':
                check_out_str = booking_data.get('check_out', '')
                
                try:
                    check_out_date = datetime.fromisoformat(check_out_str.replace('Z', '+00:00'))
                    current_date = datetime.now(check_out_date.tzinfo) if check_out_date.tzinfo else datetime.now()
                    
                    # If checkout date has passed, mark as completed
                    if check_out_date < current_date:
                        booking.reference.update({
                            'status': 'completed',
                            'completed_at': now,
                            'updated_at': now
                        })
                        updated_count += 1
                        logger.info(f"Updated booking {booking.id} to completed")
                except Exception as e:
                    logger.warning(f"Error parsing date for booking {booking.id}: {str(e)}")
        
        if updated_count > 0:
            logger.info(f"✅ Updated {updated_count} bookings to completed status")
        
        return updated_count
    except Exception as e:
        logger.error(f"Error updating expired bookings: {str(e)}")
        return 0

def log_activity(user_email, action, details=""):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_email,
        "action": action,
        "details": details
    }
    logs_collection.add(log_entry)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_transaction_id():
    """Generate unique transaction ID"""
    timestamp = int(time.time())
    random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return f"TXN{timestamp}{random_suffix}"



@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', 
                          user_email=session.get('user_email'),
                          user_name=session.get('user_name'))



@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password or not name:
            return jsonify({"success": False, "message": "All fields are required"}), 400
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        if not is_valid_password(password):
            return jsonify({
                "success": False, 
                "message": "Password must be at least 8 characters with uppercase, lowercase, and numbers"
            }), 400
        
        existing_user = users_collection.where('email', '==', email).limit(1).get()
        if list(existing_user):
            return jsonify({"success": False, "message": "Email already registered"}), 400
        
        new_user = {
            "email": email,
            "password": hash_password(password),
            "name": name,
            "created_at": datetime.now().isoformat(),
            "google_auth": False
        }
        
        users_collection.add(new_user)
        session.permanent = True
        session['user_email'] = email
        session['user_name'] = name
        
        log_activity(email, "User registered")
        logger.info(f"✅ User registered: {email}")
        
        return jsonify({"success": True, "message": "Registration successful", "redirect": "/dashboard"})
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"success": False, "message": "Registration failed"}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400
        
        users = users_collection.where('email', '==', email).limit(1).get()
        user_list = list(users)
        
        if not user_list:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        user_data = user_list[0].to_dict()
        
        if not verify_password(password, user_data['password']):
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        session.permanent = True
        session['user_email'] = email
        session['user_name'] = user_data['name']
        log_activity(email, "User logged in")
        logger.info(f"✅ User logged in: {email}")
        
        return jsonify({"success": True, "message": "Login successful"})
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": "Login failed"}), 500

@app.route('/api/google-auth', methods=['POST'])
def google_auth():
    data = request.json
    email = data.get('email')
    name = data.get('name')
    google_id = data.get('googleId')
    
    if not email or not name or not google_id:
        return jsonify({"success": False, "message": "Invalid Google authentication data"}), 400
    
    
    users = users_collection.where('email', '==', email).limit(1).get()
    user_list = list(users)
    
    if not user_list:
        
        new_user = {
            "email": email,
            "password": hash_password(google_id),
            "name": name,
            "created_at": datetime.now().isoformat(),
            "google_auth": True,
            "google_id": google_id
        }
        users_collection.add(new_user)
        log_activity(email, "User registered via Google")
    
    session['user_email'] = email
    session['user_name'] = name
    log_activity(email, "User logged in via Google")
    
    return jsonify({"success": True, "message": "Google authentication successful"})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    email = session.get('user_email')
    if email:
        log_activity(email, "User logged out")
    session.clear()
    return jsonify({"success": True})



@app.route('/api/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = rooms_collection.stream()
    rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    return jsonify(rooms_list)

@app.route('/api/rooms/available', methods=['GET'])
@login_required
def get_available_rooms():
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    

    rooms = rooms_collection.stream()
    rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    
    
    if not rooms_list:
        init_sample_rooms()
        rooms = rooms_collection.stream()
        rooms_list = [{"id": room.id, **room.to_dict()} for room in rooms]
    
    
    bookings = bookings_collection.where('status', '==', 'confirmed').stream()
    bookings_list = [booking.to_dict() for booking in bookings]
    
    
    if not bookings_list:
        return jsonify(rooms_list)
    
    available_rooms = []
    for room in rooms_list:
        is_available = True
        for booking in bookings_list:
            try:
                if (booking['room_id'] == room['id'] and 
                    not (booking['check_out'] <= check_in or booking['check_in'] >= check_out)):
                    is_available = False
                    break
            except KeyError:
            
                continue
        if is_available:
            available_rooms.append(room)
    
    return jsonify(available_rooms)



@app.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment and create transaction record"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No payment data provided"}), 400
        
        required_fields = ['billing_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode', 'payment_method', 'amount']
        for field in required_fields:
            if field not in data or not data.get(field):
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({"success": False, "message": "Invalid payment amount"}), 400
            if amount > 1000000:
                return jsonify({"success": False, "message": "Amount exceeds maximum limit"}), 400
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Invalid amount format"}), 400
        
        # Validate payment method
        valid_methods = ['card', 'upi', 'netbanking', 'wallet']
        if data.get('payment_method') not in valid_methods:
            return jsonify({"success": False, "message": "Invalid payment method"}), 400
        
        # Validate email
        if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
            return jsonify({"success": False, "message": "Invalid email format"}), 400
        
        # Validate phone (basic validation)
        phone = str(data.get('phone', ''))
        if len(phone) < 10:
            return jsonify({"success": False, "message": "Invalid phone number"}), 400
        
        transaction_id = generate_transaction_id()
        
        transaction_data = {
            "transaction_id": transaction_id,
            "user_email": session.get('user_email'),
            "user_name": session.get('user_name', ''),
            "amount": amount,
            "payment_method": data['payment_method'],
            "payment_status": "completed",
            
            "billing_name": data['billing_name'],
            "billing_email": data['email'],
            "billing_phone": phone,
            "billing_address": data['address'],
            "billing_city": data['city'],
            "billing_state": data['state'],
            "billing_zipcode": data['zipcode'],
            "billing_country": data.get('country', 'India'),
            
            "booking_data": data.get('booking_data', {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "booking_id": None
        }
        
        payment_method = data.get('payment_method')
        if payment_method == 'card':
            card_number = data.get('card_number', '')
            transaction_data['card_last4'] = card_number[-4:] if len(card_number) >= 4 else None
            transaction_data['card_type'] = data.get('card_type', 'credit')
        elif payment_method == 'netbanking':
            transaction_data['bank_name'] = data.get('bank', '')
        elif payment_method == 'upi':
            transaction_data['upi_id'] = data.get('upi_id', '')
        
        
        transactions_collection.document(transaction_id).set(transaction_data)
        
        log_activity(
            session['user_email'], 
            "Payment processed", 
            f"Transaction: {transaction_id}, Method: {payment_method}, Amount: ₹{data['amount']}"
        )
        
        print(f"✅ Payment processed: {transaction_id}")
        
        return jsonify({
            "success": True,
            "message": "Payment processed successfully",
            "transaction_id": transaction_id,
            "payment_method": payment_method,
            "amount": data['amount'],
            "status": "completed"
        })
        
    except Exception as e:
        print(f"❌ Payment processing error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Payment processing failed: {str(e)}"
        }), 500



@app.route('/api/bookings', methods=['GET', 'POST'])
@login_required
def handle_bookings():
    if request.method == 'GET':
        try:
            # Update expired bookings first
            update_expired_bookings(session['user_email'])
            
            bookings = bookings_collection.where('user_email', '==', session['user_email']).stream()
            bookings_list = [{"id": booking.id, **booking.to_dict()} for booking in bookings]
            
            # Sort by created_at descending
            bookings_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            logger.info(f"✅ Fetched {len(bookings_list)} bookings for {session['user_email']}")
            return jsonify(bookings_list)
        except Exception as e:
            logger.error(f"Get bookings error: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    elif request.method == 'POST':
        data = request.json
        
        required_fields = ['room_id', 'room_number', 'check_in', 'check_out', 'guests', 'total_price']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing field: {field}"}), 400
        
        try:
            
            new_booking = {
                "user_email": session['user_email'],
                "user_name": session.get('user_name', ''),
                "room_id": data['room_id'],
                "room_number": data['room_number'],
                "check_in": data['check_in'],
                "check_out": data['check_out'],
                "guests": data['guests'],
                "total_price": data['total_price'],
                "status": "confirmed",
                "created_at": datetime.now().isoformat(),
                
                
                "payment_method": data.get('payment_method', 'card'),
                "payment_status": data.get('payment_status', 'completed'),
                "transaction_id": data.get('transaction_id', None)  
            }
            
            
            doc_ref = bookings_collection.add(new_booking)
            booking_id = doc_ref[1].id
            new_booking['id'] = booking_id
            
            
            if new_booking.get('transaction_id'):
                try:
                    transaction_ref = transactions_collection.document(new_booking['transaction_id'])
                    transaction_ref.update({
                        "booking_id": booking_id,
                        "updated_at": datetime.now().isoformat()
                    })
                    print(f"✅ Transaction {new_booking['transaction_id']} updated with booking_id: {booking_id}")
                except Exception as e:
                    print(f"⚠️ Could not update transaction: {str(e)}")
            
            log_activity(
                session['user_email'], 
                "Booking created", 
                f"Room {data['room_number']}, Transaction: {new_booking.get('transaction_id', 'N/A')}"
            )
            
            print(f"✅ Booking created: {booking_id}")
            
            return jsonify({"success": True, "booking": new_booking})
            
        except Exception as e:
            print(f"❌ Booking creation error: {str(e)}")
            return jsonify({"success": False, "message": f"Booking failed: {str(e)}"}), 500

@app.route('/api/bookings/<booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        booking_ref = bookings_collection.document(booking_id)
        booking = booking_ref.get()
        
        if not booking.exists:
            return jsonify({"success": False, "message": "Booking not found"}), 404
        
        booking_data = booking.to_dict()
        
        if booking_data['user_email'] != session['user_email']:
            return jsonify({"success": False, "message": "Unauthorized"}), 403
        
        booking_ref.update({
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat()
        })
        
        if booking_data.get('transaction_id'):
            try:
                transaction_ref = transactions_collection.document(booking_data['transaction_id'])
                transaction_ref.update({
                    "payment_status": "refunded",
                    "updated_at": datetime.now().isoformat()
                })
                logger.info(f"✅ Transaction {booking_data['transaction_id']} marked as refunded")
            except Exception as e:
                logger.warning(f"Could not update transaction: {str(e)}")
        
        log_activity(session['user_email'], "Booking cancelled", f"Booking ID: {booking_id}")
        logger.info(f"✅ Booking {booking_id} cancelled")
        
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Cancel booking error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/dashboard-stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    try:
        # Update expired bookings first
        update_expired_bookings(session['user_email'])
        
        bookings = bookings_collection.where('user_email', '==', session['user_email']).stream()
        user_bookings = [{"id": booking.id, **booking.to_dict()} for booking in bookings]
        
        # Sort by created_at descending
        user_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Calculate active bookings (confirmed status AND checkout date in future)
        now = datetime.now()
        active_count = 0
        
        for booking in user_bookings:
            if booking.get('status') == 'confirmed':
                try:
                    check_out_str = booking.get('check_out', '')
                    check_out_date = datetime.fromisoformat(check_out_str.replace('Z', '+00:00'))
                    current_date = datetime.now(check_out_date.tzinfo) if check_out_date.tzinfo else now
                    
                    if check_out_date > current_date:
                        active_count += 1
                except Exception as e:
                    logger.warning(f"Error parsing checkout date: {str(e)}")
        
        stats = {
            "total_bookings": len(user_bookings),
            "active_bookings": active_count,  # Only count future bookings
            "total_spent": sum(b['total_price'] for b in user_bookings if b['status'] == 'confirmed'),
            "recent_bookings": user_bookings[:5]
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    """Get all transactions for current user"""
    transactions = transactions_collection.where('user_email', '==', session['user_email']).stream()
    transactions_list = [{"id": trans.id, **trans.to_dict()} for trans in transactions]
    

    transactions_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return jsonify(transactions_list)

@app.route('/api/transactions/<transaction_id>', methods=['GET'])
@login_required
def get_transaction(transaction_id):
    """Get specific transaction details"""
    transaction_ref = transactions_collection.document(transaction_id)
    transaction = transaction_ref.get()
    
    if not transaction.exists:
        return jsonify({"success": False, "message": "Transaction not found"}), 404
    
    transaction_data = transaction.to_dict()
    
    
    if transaction_data['user_email'] != session['user_email']:
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    transaction_data['id'] = transaction_id
    return jsonify({"success": True, "transaction": transaction_data})



@app.route('/api/reset-rooms')
@login_required
def reset_rooms():
    """Reset all rooms to default state"""
    
    rooms = rooms_collection.stream()
    for room in rooms:
        room.reference.delete()
    
    
    init_sample_rooms()
    return jsonify({"success": True, "message": "Rooms have been reset"})

@app.route('/api/chatbot/message', methods=['POST'])
@login_required
def chatbot_message():
    """
    Process chatbot message and return response
    """
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({
                "success": False,
                "message": "Empty message"
            }), 400
        
        # Get user email from session
        user_email = session.get('user_email')
        
        # Process message through chatbot
        bot_response = get_bot_response(message, user_email)
        
        # Store conversation in Firestore for learning/improvement
        conversation_data = {
            "user_email": user_email,
            "user_message": message,
            "bot_response": bot_response['response'],
            "intent": bot_response.get('intent'),
            "confidence": bot_response.get('confidence'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to Firestore (optional - for analytics)
        try:
            db.collection('chatbot_conversations').add(conversation_data)
        except Exception as e:
            print(f"⚠️ Could not save conversation: {str(e)}")
        
        # Log activity
        log_activity(user_email, "Chatbot interaction", f"Intent: {bot_response.get('intent')}")
        
        return jsonify({
            "success": True,
            "response": bot_response['response'],
            "intent": bot_response.get('intent'),
            "confidence": bot_response.get('confidence'),
            "suggestions": bot_response.get('suggestions', []),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Chatbot error: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Sorry, I encountered an error. Please try again.",
            "error": str(e)
        }), 500


@app.route('/api/chatbot/suggestions', methods=['GET'])
@login_required
def chatbot_suggestions():
    """
    Get suggested questions for the chatbot
    """
    try:
        suggestions = chatbot_instance.get_suggested_questions()
        return jsonify({
            "success": True,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/chatbot/history', methods=['GET'])
@login_required
def chatbot_history():
    """
    Get user's chat history
    """
    try:
        user_email = session.get('user_email')
        
        # Get last 50 conversations
        conversations = db.collection('chatbot_conversations')\
            .where('user_email', '==', user_email)\
            .order_by('timestamp', direction=firestore.Query.DESCENDING)\
            .limit(50)\
            .stream()
        
        history = []
        for conv in conversations:
            conv_data = conv.to_dict()
            history.append({
                "id": conv.id,
                "user_message": conv_data.get('user_message'),
                "bot_response": conv_data.get('bot_response'),
                "timestamp": conv_data.get('timestamp')
            })
        
        return jsonify({
            "success": True,
            "history": history
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route('/api/chatbot/feedback', methods=['POST'])
@login_required
def chatbot_feedback():
    """
    Collect user feedback on chatbot responses
    """
    try:
        data = request.json
        conversation_id = data.get('conversation_id')
        rating = data.get('rating')  # 1-5 or thumbs up/down
        feedback_text = data.get('feedback', '')
        
        feedback_data = {
            "conversation_id": conversation_id,
            "user_email": session.get('user_email'),
            "rating": rating,
            "feedback_text": feedback_text,
            "timestamp": datetime.now().isoformat()
        }
        
        db.collection('chatbot_feedback').add(feedback_data)
        
        return jsonify({
            "success": True,
            "message": "Thank you for your feedback!"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """Subscribe to newsletter - Firebase version"""
    try:
        # Get email from request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False, 
                'message': 'No data received'
            }), 400
        
        email = data.get('email', '').strip().lower()
        
        # Validate email format
        if not email:
            return jsonify({
                'success': False, 
                'message': 'Email is required'
            }), 400
        
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({
                'success': False, 
                'message': 'Invalid email format'
            }), 400
        
        # Check if already subscribed in Firebase
        try:
            subscribers_ref = db.collection('newsletter_subscribers')
            existing = subscribers_ref.where('email', '==', email).limit(1).get()
            
            if len(list(existing)) > 0:
                return jsonify({
                    'success': False, 
                    'message': 'already_subscribed'
                }), 200
        except Exception as check_error:
            print(f"Firebase check error: {check_error}")
            # Continue even if check fails
        
        # Create subscriber document
        from datetime import datetime
        import time
        
        subscriber = {
            'email': email,
            'subscribed_at': datetime.utcnow().isoformat(),
            'timestamp': time.time(),
            'status': 'active',
            'source': 'website_footer',
            'ip_address': request.remote_addr if hasattr(request, 'remote_addr') else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown') if hasattr(request, 'headers') else 'unknown'
        }
        
        # Save to Firebase Firestore
        try:
            doc_ref = db.collection('newsletter_subscribers').document()
            doc_ref.set(subscriber)
            
            print(f"✅ New newsletter subscriber: {email} (ID: {doc_ref.id})")
            
        except Exception as firebase_error:
            print(f"Firebase insert error: {firebase_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False, 
                'message': f'Database error: {str(firebase_error)}'
            }), 500
        
        return jsonify({
            'success': True, 
            'message': 'Successfully subscribed to newsletter',
            'email': email
        }), 200
        
    except Exception as e:
        print(f"❌ Newsletter subscription error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/chatbot/transfer', methods=['POST'])
@login_required
def chatbot_transfer():
    """
    Transfer chat to human agent
    """
    try:
        data = request.json
        reason = data.get('reason', 'User requested transfer')
        conversation_context = data.get('context', [])
        
        transfer_data = {
            "user_email": session.get('user_email'),
            "user_name": session.get('user_name'),
            "reason": reason,
            "conversation_context": conversation_context,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Save transfer request
        transfer_ref = db.collection('agent_transfers').add(transfer_data)
        
        # Log activity
        log_activity(
            session.get('user_email'),
            "Agent transfer requested",
            reason
        )
        
        return jsonify({
            "success": True,
            "message": "Transfer request created. An agent will join shortly.",
            "transfer_id": transfer_ref[1].id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/admin/newsletter')
@login_required
def admin_newsletter():
    """View newsletter subscribers (ADMIN ONLY - test1@gmail.com)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return redirect('/dashboard')
        
        # Get all subscribers from Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        
        subscribers = []
        for doc in docs:
            sub_data = doc.to_dict()
            sub_data['id'] = doc.id
            subscribers.append(sub_data)
        
        # Count statistics
        total_subscribers = len(subscribers)
        active_subscribers = len([s for s in subscribers if s.get('status') == 'active'])
        
        stats = {
            'total': total_subscribers,
            'active': active_subscribers,
            'unsubscribed': total_subscribers - active_subscribers
        }
        
        return render_template('admin_newsletter.html', 
                             subscribers=subscribers, 
                             stats=stats)
    except Exception as e:
        print(f"Error loading newsletter admin: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading subscribers: {str(e)}", 500


@app.route('/api/newsletter/export')
@login_required
def export_newsletter():
    """Export newsletter subscribers as JSON (ADMIN ONLY)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Get all subscribers from Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        
        subscribers = []
        for doc in docs:
            sub_data = doc.to_dict()
            sub_data['id'] = doc.id
            subscribers.append(sub_data)
        
        return jsonify({
            'success': True,
            'subscribers': subscribers
        }), 200
        
    except Exception as e:
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Export failed: {str(e)}'
        }), 500


@app.route('/api/newsletter/check-subscription', methods=['POST'])
def check_newsletter_subscription():
    """Check if user is subscribed to newsletter"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'subscribed': False}), 200
        
        # Check in Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.where('email', '==', email).where('status', '==', 'active').limit(1).get()
        
        is_subscribed = len(list(docs)) > 0
        
        return jsonify({'subscribed': is_subscribed}), 200
        
    except Exception as e:
        print(f"Check subscription error: {e}")
        return jsonify({'subscribed': False}), 200


@app.route('/api/newsletter/unsubscribe', methods=['POST'])
def unsubscribe_newsletter():
    """Unsubscribe from newsletter"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400
        
        # Find subscriber in Firebase
        subscribers_ref = db.collection('newsletter_subscribers')
        docs = subscribers_ref.where('email', '==', email).limit(1).get()
        
        found = False
        for doc in docs:
            # Update status to unsubscribed
            doc.reference.update({
                'status': 'unsubscribed',
                'unsubscribed_at': datetime.utcnow().isoformat()
            })
            found = True
            print(f"✅ Unsubscribed: {email}")
            break
        
        if not found:
            return jsonify({
                'success': False,
                'message': 'Email not found in subscriber list'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Successfully unsubscribed'
        }), 200
        
    except Exception as e:
        print(f"Unsubscribe error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/api/admin/all-bookings', methods=['GET'])
@login_required
def get_all_bookings():
    """Get all bookings from all users (ADMIN ONLY)"""
    try:
        # Check if user is admin
        if session.get('user_email') != 'test1@gmail.com':
            return jsonify({
                "success": False,
                "message": "Unauthorized. Admin access only."
            }), 403
        
        # Fetch all bookings from Firebase
        bookings = bookings_collection.stream()
        all_bookings = []
        
        for booking in bookings:
            booking_data = booking.to_dict()
            booking_data['id'] = booking.id
            all_bookings.append(booking_data)
        
        # Sort by created_at (newest first)
        all_bookings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        log_activity(
            session['user_email'], 
            "Admin: Downloaded all bookings report", 
            f"Total bookings: {len(all_bookings)}"
        )
        
        print(f"✅ Admin {session['user_email']} exported {len(all_bookings)} bookings")
        
        return jsonify({
            "success": True,
            "bookings": all_bookings,
            "total_count": len(all_bookings)
        })
        
    except Exception as e:
        print(f"❌ Error fetching all bookings: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error fetching bookings: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    init_sample_rooms()
    
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)
