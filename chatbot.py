# chatbot.py - Intelligent Hotel Support Chatbot (CORRECTED)
import sys
import os
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import requests
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
import random
import logging

logger = logging.getLogger(__name__)

class HotelSupportBot:
    def __init__(self):
        """Initialize the chatbot with knowledge base"""
        self.knowledge_base = self._load_knowledge_base()
        
        # Load and merge expanded knowledge (if available)
        try:
            from training_data import EXPANDED_KNOWLEDGE_BASE
            self.knowledge_base.update(EXPANDED_KNOWLEDGE_BASE)
            print("✅ Expanded knowledge base loaded successfully!")
        except ImportError:
            print("ℹ️ Using default knowledge base (training_data.py not found)")
        except Exception as e:
            print(f"⚠️ Error loading expanded knowledge: {str(e)}")

        self.context = {}
        self.greetings = [
            "Hello! I'm your Nur-e-Haya luxury concierge. How may I assist you today?",
            "Welcome to Nur-e-Haya! I'm here 24/7 to help you with reservations, amenities, dining, and hotel services.",
            "Greetings! How may I assist you with your stay or booking at Nur-e-Haya today?"
        ]
        self.fallback_responses = [
            "I'm here to assist you with everything at Nur-e-Haya! 🏨\n\nHere are some popular topics you can ask me about:\n• **Rooms & Pricing**: Single (₹2,500), Double (₹4,000), Suite (₹5,000), Luxury (₹8,000)\n• **Check-in/Out**: Check-in from 2:00 PM, Check-out by 11:00 AM\n• **Amenities**: WiFi, Swimming Pool, Luxury Spa, 24/7 Room Service\n• **Dining**: In-house gourmet restaurant, buffet breakfast, and 24/7 dining menu\n• **Reservations**: Easy online booking with free 48h cancellation\n\nWhat would you like to know more about?",
            "Welcome to Nur-e-Haya Concierge! ✨\n\nI can help you explore room options, view dining menus, check facility hours, or assist with your reservation. You can also reach our front desk directly at +91 8010572845.\n\nHow may I help make your stay exceptional?",
            "Thank you for contacting Nur-e-Haya Luxury Support! 🌟\n\nWhether you need help booking a room, checking our cancellation policy, arranging airport transportation, or ordering room service, I'm here 24/7 to assist. What information can I provide for you today?"
        ]
        
    def _load_knowledge_base(self):
        """Load comprehensive hotel knowledge base"""
        return {
            # Booking & Reservations
            "booking": {
                "keywords": ["book", "booking", "reserve", "reservation", "room", "availability", "available"],
                "patterns": [
                    r"how (do|can) i book",
                    r"make (a )?reservation",
                    r"room available",
                    r"check availability"
                ],
                "responses": [
                    "To book a room, click on 'NEW BOOKING' in the navigation menu, select your check-in/check-out dates, choose your preferred room, and complete the payment process. It's quick and secure!",
                    "You can easily book through our dashboard! Navigate to 'NEW BOOKING', select your dates, pick from our available rooms (Single, Double, Suite, Luxury, or Family), and proceed with secure payment.",
                    "Booking is simple: Go to NEW BOOKING → Choose dates → Select room type → Review details → Complete payment. All bookings are instantly confirmed!"
                ]
            },
            
            # Check-in/Check-out
            "checkin_checkout": {
                "keywords": ["check in", "check out", "check-in", "check-out", "arrival", "departure", "time"],
                "patterns": [
                    r"check.?in (time|timing)",
                    r"check.?out (time|timing)",
                    r"what time (can i|do i)",
                    r"when (can i|do i) check"
                ],
                "responses": [
                    "Our standard check-in time is 2:00 PM and check-out is at 11:00 AM. Early check-in or late check-out may be available based on room availability - just ask!",
                    "Check-in: 2:00 PM onwards | Check-out: 11:00 AM. Need early check-in or late check-out? Contact us and we'll do our best to accommodate your needs!",
                    "You can check in from 2:00 PM and check-out is at 11:00 AM. For any timing adjustments, please contact our front desk in advance."
                ]
            },
            
            # Cancellation Policy
            "cancellation": {
                "keywords": ["cancel", "cancellation", "refund", "policy"],
                "patterns": [
                    r"cancel(lation)? policy",
                    r"how to cancel",
                    r"get (a )?refund",
                    r"cancellation charges"
                ],
                "responses": [
                    "Our cancellation policy:\n• 48+ hours before check-in: Full refund\n• 24-48 hours: 50% refund\n• Within 24 hours: No refund\n\nTo cancel, go to 'MY BOOKINGS' and click the cancel button.",
                    "You can cancel anytime! Free cancellation if done 48+ hours before arrival. Partial refund (50%) for 24-48 hours notice. Cancellations within 24 hours are non-refundable.",
                    "Cancellation is easy through 'MY BOOKINGS'. Full refund for 48+ hour notice, 50% for 24-48 hours, and no refund within 24 hours of check-in."
                ]
            },
            
            # Room Types & Prices
            "rooms": {
                "keywords": ["room", "suite", "single", "double", "luxury", "family", "price", "cost", "rate"],
                "patterns": [
                    r"room types",
                    r"how much (is|does|cost)",
                    r"price (of|for)",
                    r"what rooms"
                ],
                "responses": [
                    "We offer 5 room types:\n• Single Room: ₹2,500/night (1 guest)\n• Double Room: ₹4,000/night (2 guests)\n• Suite: ₹5,000/night (3 guests)\n• Luxury Room: ₹8,000/night (4 guests)\n• Family Room: ₹2,000/night (4 guests)\n\nAll rooms include WiFi, AC, TV & room service!",
                    "Our accommodations range from ₹2,000 to ₹8,000 per night. Choose from Single, Double, Suite, Luxury, or Family rooms - each with premium amenities tailored to your needs!",
                    "Room rates:\n₹2,000-2,500: Single/Family\n₹4,000: Double\n₹5,000: Suite\n₹8,000: Luxury\n\nAll include complimentary WiFi, AC, TV, and 24/7 room service!"
                ]
            },
            
            # Amenities
            "amenities": {
                "keywords": ["amenity", "amenities", "facility", "facilities", "wifi", "gym", "pool", "spa", "parking"],
                "patterns": [
                    r"what amenities",
                    r"do you have (a )?wifi",
                    r"is there (a )?(gym|pool|spa)",
                    r"facilities available"
                ],
                "responses": [
                    "All rooms include: WiFi, AC, TV, and Room Service. Higher-tier rooms offer Mini Bar, Jacuzzi, Ocean Views, and Butler Service. Hotel amenities include 24/7 front desk, restaurant, and concierge services!",
                    "Standard amenities in every room: High-speed WiFi, Air conditioning, Smart TV, Room service. Luxury upgrades include Mini bars, Jacuzzis, Premium views, and dedicated Butler service!",
                    "We provide: Complimentary WiFi throughout, Climate-controlled rooms, Modern entertainment systems, 24/7 room service. Premium rooms add exclusive features like Jacuzzis and butler service!"
                ]
            },
            
            # Payment Methods
            "payment": {
                "keywords": ["payment", "pay", "card", "upi", "netbanking", "wallet", "method"],
                "patterns": [
                    r"payment (method|option)",
                    r"how (can|do) i pay",
                    r"accept (upi|card|netbanking)",
                    r"payment gateway"
                ],
                "responses": [
                    "We accept all major payment methods:\n✓ Credit/Debit Cards (Visa, Mastercard, Amex)\n✓ Net Banking (All major banks)\n✓ UPI (PhonePe, Google Pay, Paytm, BHIM)\n✓ Digital Wallets (Paytm, PhonePe, Amazon Pay)\n\nAll transactions are 256-bit SSL encrypted!",
                    "Multiple payment options available: Cards, Net Banking, UPI, and Digital Wallets. Choose what's convenient! All payments are secure with industry-standard encryption.",
                    "Pay your way! We support Cards (Visa/Mastercard/Amex), UPI IDs & QR codes, Net Banking from 100+ banks, and popular wallets. 100% secure payments guaranteed!"
                ]
            },
            
            # Contact & Support
            "contact": {
                "keywords": ["contact", "phone", "email", "call", "reach", "support", "help"],
                "patterns": [
                    r"contact (you|number|details)",
                    r"phone number",
                    r"email address",
                    r"how to reach"
                ],
                "responses": [
                    "Reach us anytime:\n📞 Phone: +91 8010572845 (24/7)\n📧 Email: support@nur-e-haya.com\n💬 Live Chat: Available on dashboard\n\nOur team responds within 24 hours!",
                    "We're always here for you!\nCall: +91 8010572845\nEmail: support@nur-e-haya.com\nChat: Use the chat bubble on your dashboard\n\nSupport available 24/7!",
                    "Contact our 24/7 support team:\n• Phone: +91 8010572845\n• Email: support@nur-e-haya.com\n• Live Chat: Dashboard → Chat icon\n• Response time: Within 24 hours"
                ]
            },
            
            # Location & Transportation
            "location": {
                "keywords": ["location", "address", "where", "airport", "shuttle", "transport", "pickup"],
                "patterns": [
                    r"where (are you|is hotel)",
                    r"hotel (location|address)",
                    r"airport (shuttle|pickup|transfer)",
                    r"how to reach"
                ],
                "responses": [
                    "We're centrally located for easy access! Complimentary airport shuttle available - book 24 hours in advance. Local transportation and taxi services readily available at our concierge desk.",
                    "Location: Easily accessible from major transit points. We offer FREE airport pickup/drop - just inform us 24 hours before arrival. Our concierge can arrange all your transportation needs!",
                    "Getting here is easy! We provide complimentary airport shuttle service (advance booking required). Once here, our concierge can arrange taxis, rental cars, or guided tours!"
                ]
            },
            
            # Special Requests
            "special_requests": {
                "keywords": ["special", "request", "requirement", "need", "arrange"],
                "patterns": [
                    r"special (request|requirement)",
                    r"can you arrange",
                    r"i need (a |an )?",
                    r"extra (bed|pillow|towel)"
                ],
                "responses": [
                    "We're happy to accommodate special requests! Mention your needs during booking or contact us directly. Popular requests: Extra bedding, dietary preferences, celebration arrangements, accessibility needs.",
                    "Your comfort matters! Add special requests during booking or email support@nur-e-haya.com. We arrange: Room preferences, Extra amenities, Celebration setups, Dietary accommodations, and more!",
                    "Special requirements? No problem! Include them in the 'Special Requests' field during booking. Need something specific? Email us or call +91 8010572845!"
                ]
            },
            
            # Pets Policy
            "pets": {
                "keywords": ["pet", "pets", "dog", "cat", "animal"],
                "patterns": [
                    r"(can i|do you) (bring|allow) pets",
                    r"pet (policy|friendly)",
                    r"bring (my )?(dog|cat)"
                ],
                "responses": [
                    "We love animals! However, to ensure comfort for all guests, we don't permit pets except registered service animals. We can recommend excellent nearby pet care facilities if needed.",
                    "For the comfort of all guests, pets are not allowed except certified service animals. Need pet care recommendations? Our concierge can suggest trusted local facilities!",
                    "Service animals are always welcome! Unfortunately, we cannot accommodate other pets to maintain comfort for all guests. We're happy to recommend pet boarding services nearby."
                ]
            },
            
            # Dining
            "dining": {
                "keywords": ["food", "restaurant", "breakfast", "lunch", "dinner", "dining", "meal"],
                "patterns": [
                    r"(do you have|is there) (a )?restaurant",
                    r"breakfast included",
                    r"room service",
                    r"food (available|options)"
                ],
                "responses": [
                    "Culinary delights await! We offer 24/7 room service, in-house restaurant with diverse cuisine, and special dietary options. Breakfast packages available upon request!",
                    "Dining options: 24/7 room service to your door, On-site restaurant with multi-cuisine menu, Special dietary accommodations, Complimentary breakfast (select packages). Bon appétit!",
                    "Enjoy delicious meals! Our restaurant serves breakfast, lunch & dinner. 24/7 room service also available. Vegetarian, vegan & special dietary requests? We've got you covered!"
                ]
            },
            
            # Loyalty Program
            "loyalty": {
                "keywords": ["loyalty", "points", "rewards", "discount", "offer", "promo"],
                "patterns": [
                    r"loyalty (program|points)",
                    r"(any )?(discount|offer|promo)",
                    r"rewards program",
                    r"promo code"
                ],
                "responses": [
                    "Join our rewards program! Earn points with every booking visible on your dashboard. Current promo codes: WELCOME10 (10% off), SAVE500 (₹500 off), LUXURY20 (20% off luxury rooms). Check your dashboard for personalized offers!",
                    "Loyalty perks await! Automatic points on bookings, Exclusive member discounts, Early access to offers, Special occasion rewards. Try codes: WELCOME10, SAVE500, LUXURY20 at checkout!",
                    "Rewards Program benefits: Points for every stay, Redeemable for discounts, Special member rates, Birthday surprises! Active codes: WELCOME10, SAVE500, LUXURY20. Enter at payment!"
                ]
            },
            
            # Safety & Security
            "safety": {
                "keywords": ["safe", "safety", "security", "secure", "covid", "hygiene", "clean"],
                "patterns": [
                    r"(is it|are you) safe",
                    r"safety (measure|protocol)",
                    r"covid (protocol|safe)",
                    r"hygiene standard"
                ],
                "responses": [
                    "Your safety is paramount! We maintain:\n✓ Enhanced cleaning protocols\n✓ 24/7 security surveillance\n✓ Contactless check-in options\n✓ Sanitized rooms\n✓ Staff health monitoring\n✓ Emergency response systems\n\nYour wellbeing is our priority!",
                    "Safety measures in place: Round-the-clock security, Enhanced sanitization, Health-screened staff, Contactless services, In-room safety features, Emergency protocols. Sleep soundly knowing you're secure!",
                    "We ensure: 24/7 trained security, Medical-grade cleanliness, COVID-safe practices, In-room safes, Fire safety systems, Emergency assistance. Your safety and peace of mind guaranteed!"
                ]
            },
            
            # Modify Booking
            "modify": {
                "keywords": ["modify", "change", "update", "edit", "reschedule"],
                "patterns": [
                    r"(modify|change|update) (my )?booking",
                    r"reschedule",
                    r"change (date|room)",
                    r"edit reservation"
                ],
                "responses": [
                    "To modify your booking: Go to 'MY BOOKINGS' → Select your reservation → For date/room changes, cancel the existing booking (subject to cancellation policy) and create a new one. For minor changes, contact support@nur-e-haya.com.",
                    "Need changes? Visit MY BOOKINGS on your dashboard. For major modifications (dates/rooms), you'll need to cancel and rebook. For small adjustments, email support@nur-e-haya.com or call us!",
                    "Modification process: Access MY BOOKINGS, select your reservation. Date/room changes require cancellation and rebooking (standard cancellation policy applies). For guest count or special requests, email support@nur-e-haya.com!"
                ]
            }
        }
    
    def _calculate_similarity(self, str1, str2):
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def _extract_intent(self, message):
        """Extract user intent using optimized multi-pattern NLP and keyword scoring"""
        message_lower = message.lower().strip()

        # Optional Hugging Face check if API key is explicitly configured
        hf_token = os.environ.get('HUGGINGFACE_API_KEY')
        if hf_token:
            try:
                API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
                candidate_labels = list(self.knowledge_base.keys())[:10]
                response = requests.post(
                    API_URL,
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {hf_token}"},
                    json={"inputs": message, "parameters": {"candidate_labels": candidate_labels}},
                    timeout=2
                )
                if response.status_code == 200:
                    result = response.json()
                    if result.get('scores') and result['scores'][0] > 0.45:
                        return result['labels'][0]
            except Exception as e:
                logger.debug(f"Hugging Face notice: {str(e)}")

        best_match = None
        best_score = 0.0

        for category, data in self.knowledge_base.items():
            score = 0.0

            # 1. Regex patterns (high confidence)
            patterns = data.get("patterns", [])
            for pattern in patterns:
                try:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        score += 4.0
                except Exception:
                    pass

            # 2. Keywords / Primary keywords
            keywords = data.get("keywords", data.get("primary_keywords", []))
            for kw in keywords:
                kw_clean = kw.lower().strip()
                if kw_clean and kw_clean in message_lower:
                    if re.search(r'\b' + re.escape(kw_clean) + r'\b', message_lower):
                        score += 3.0
                    else:
                        score += 1.5

            # 3. Secondary keywords
            secondary_keywords = data.get("secondary_keywords", [])
            for skw in secondary_keywords:
                skw_clean = skw.lower().strip()
                if skw_clean and skw_clean in message_lower:
                    if re.search(r'\b' + re.escape(skw_clean) + r'\b', message_lower):
                        score += 2.0
                    else:
                        score += 1.0

            # 4. Variations
            variations = data.get("variations", [])
            for var in variations:
                if var.lower() in message_lower:
                    score += 3.5

            # 5. Semantic string similarity
            cat_clean = category.replace('_', ' ')
            similarity = self._calculate_similarity(cat_clean, message_lower)
            if similarity > 0.45:
                score += similarity * 2.0

            if score > best_score:
                best_score = score
                best_match = category

        return best_match if best_score >= 1.2 else None
    
    def _get_response(self, intent):
        """Get appropriate response for detected intent"""
        if intent and intent in self.knowledge_base:
            responses = self.knowledge_base[intent].get("responses", [])
            if isinstance(responses, list) and responses:
                return random.choice(responses)
            elif isinstance(responses, str):
                return responses
        return None
    
    def _handle_greeting(self, message):
        """Detect and respond to greetings"""
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste", "hola", "greetings"]
        message_lower = message.lower().strip()
        words = message_lower.split()
        
        for greeting in greetings:
            if greeting in words or message_lower.startswith(greeting) or re.search(r'\b' + re.escape(greeting) + r'\b', message_lower):
                return random.choice(self.greetings)
        return None
    
    def _handle_thanks(self, message):
        """Detect and respond to gratitude"""
        thanks = ["thank", "thanks", "appreciate", "grateful", "thankyou"]
        message_lower = message.lower()
        
        for thank in thanks:
            if thank in message_lower:
                return random.choice([
                    "You're very welcome! Is there anything else I can help you with today?",
                    "Happy to assist you! Feel free to ask if you have more questions about Nur-e-Haya.",
                    "My absolute pleasure! Let me know if you need assistance with rooms, dining, or amenities.",
                    "Glad I could help! Don't hesitate to reach out anytime during your stay."
                ])
        return None
    
    def _handle_goodbye(self, message):
        """Detect and respond to farewells"""
        goodbyes = ["bye", "goodbye", "see you", "thanks bye", "that's all", "good night"]
        message_lower = message.lower()
        
        for goodbye in goodbyes:
            if goodbye in message_lower:
                return random.choice([
                    "Goodbye! Have a wonderful day. We look forward to hosting you at Nur-e-Haya! 🌟",
                    "Thank you for chatting with us! If you need anything else, our concierge is always here 24/7. Have a great day! ✨",
                    "Farewell! We can't wait to welcome you to Nur-e-Haya Luxury Resort. Safe travels! 🏨",
                    "Take care! Feel free to return anytime you have questions. Wishing you a pleasant experience! 😊"
                ])
        return None

    def _handle_identity(self, message):
        """Detect questions about bot identity and capabilities"""
        patterns = [
            r"who are you", r"what are you", r"your name", r"what can you do", r"tell me about yourself", r"are you (a )?bot", r"are you (an )?ai"
        ]
        message_lower = message.lower()
        for p in patterns:
            if re.search(p, message_lower):
                return (
                    "I am the AI Concierge of Nur-e-Haya Luxury Hotel & Spa! 🏨✨\n\n"
                    "I can assist you 24/7 with:\n"
                    "• **Rooms & Suites**: Details and rates for Single, Double, Suite, Luxury, & Family rooms\n"
                    "• **Reservations**: Booking procedures, modifications, and instant confirmations\n"
                    "• **Policies**: Check-in (2:00 PM), Check-out (11:00 AM), & free cancellation rules\n"
                    "• **Dining**: In-house fine dining, buffet breakfast, and 24/7 room service\n"
                    "• **Amenities**: High-speed WiFi, Infinity Pool, Luxury Spa, & Airport Shuttles\n"
                    "• **Direct Contact**: 24/7 Front Desk at +91 8010572845\n\n"
                    "How can I help you right now?"
                )
        return None

    def _handle_wellbeing(self, message):
        """Detect questions like how are you"""
        patterns = [r"how are you", r"how('s| is) it going", r"how do you do", r"how are u"]
        message_lower = message.lower()
        for p in patterns:
            if re.search(p, message_lower):
                return (
                    "I'm doing wonderful, thank you for asking! 😊\n\n"
                    "I'm delighted to help you experience the very best of Nur-e-Haya. Are you planning a new reservation or inquiring about your stay?"
                )
        return None
    
    def _handle_confusion(self, message):
        """Detect confusion and offer help"""
        confusion = ["confused", "don't understand", "not clear", "what", "huh", "help"]
        message_lower = message.lower().strip()
        
        for word in confusion:
            if word in message_lower and len(message.split()) < 5:
                return random.choice([
                    "I'm here to help! You can ask me about:\n• Booking rooms & real-time rates\n• Check-in/out times (2 PM / 11 AM)\n• Cancellation & refund policies\n• Dining menus & room service\n• Payment methods (Cards, UPI, NetBanking)\n\nWhat would you like to know?",
                    "Let me assist you! I can help with room reservations, hotel amenities, payments, and dining. What specific information do you need?",
                    "No worries at all! Feel free to ask about our luxury rooms, booking dates, facilities, or contact details. How can I assist you?"
                ])
        return None
    
    def process_message(self, message, user_email=None):
        """
        Process user message and generate appropriate response
        
        Args:
            message (str): User's message
            user_email (str): User's email for context (optional)
            
        Returns:
            dict: Response with message and metadata
        """
        if user_email:
            self.context[user_email] = {
                "last_message": message,
                "timestamp": datetime.now().isoformat()
            }
        
        if not message or not message.strip():
            return {
                "response": "I didn't catch that. Could you please type your question?",
                "intent": None,
                "confidence": 0,
                "suggestions": self.get_suggested_questions()[:4]
            }
        
        # 1. Check Identity / Who are you
        identity_response = self._handle_identity(message)
        if identity_response:
            return {
                "response": identity_response,
                "intent": "identity",
                "confidence": 1.0,
                "suggestions": ["Room types & prices", "Check-in times", "Dining menu", "Cancellation policy"]
            }

        # 2. Check Wellbeing / How are you
        wellbeing_response = self._handle_wellbeing(message)
        if wellbeing_response:
            return {
                "response": wellbeing_response,
                "intent": "wellbeing",
                "confidence": 1.0,
                "suggestions": ["How do I book a room?", "What are your room rates?", "Do you have a pool?"]
            }

        # 3. Check Greetings
        greeting_response = self._handle_greeting(message)
        if greeting_response:
            return {
                "response": greeting_response,
                "intent": "greeting",
                "confidence": 1.0,
                "suggestions": ["What are your room rates?", "Check-in and check-out times?", "Is breakfast included?"]
            }
        
        # 4. Check Thanks
        thanks_response = self._handle_thanks(message)
        if thanks_response:
            return {
                "response": thanks_response,
                "intent": "gratitude",
                "confidence": 1.0,
                "suggestions": ["Explore luxury rooms", "View hotel facilities", "Contact front desk"]
            }
        
        # 5. Check Goodbye
        goodbye_response = self._handle_goodbye(message)
        if goodbye_response:
            return {
                "response": goodbye_response,
                "intent": "farewell",
                "confidence": 1.0,
                "suggestions": []
            }
        
        # 6. Check Confusion
        confusion_response = self._handle_confusion(message)
        if confusion_response:
            return {
                "response": confusion_response,
                "intent": "help",
                "confidence": 1.0,
                "suggestions": self.get_suggested_questions()[:4]
            }
        
        # 7. Extract intent from knowledge base
        intent = self._extract_intent(message)
        
        if intent:
            response = self._get_response(intent)
            if response:
                return {
                    "response": response,
                    "intent": intent,
                    "confidence": 0.88,
                    "suggestions": [
                        "How do I book a room?",
                        "What are your check-in times?",
                        "What is your cancellation policy?",
                        "What payment methods do you accept?"
                    ]
                }
        
        # 8. Dynamic Fallback response with rotating answers
        return {
            "response": random.choice(self.fallback_responses),
            "intent": "unknown",
            "confidence": 0.35,
            "suggestions": [
                "How do I book a room?",
                "What are your room rates?",
                "What are your check-in times?",
                "What is your cancellation policy?"
            ]
        }
    
    def get_suggested_questions(self):
        """Get list of suggested questions users can ask"""
        return [
            "How do I book a room?",
            "What are the check-in and check-out times?",
            "What is your cancellation policy?",
            "What room types and prices do you offer?",
            "What payment methods do you accept?",
            "How can I contact customer support?",
            "Do you offer airport shuttle service?",
            "Can I bring my pet?",
            "Is breakfast included?",
            "How do I modify my booking?"
        ]

# Singleton instance
chatbot_instance = HotelSupportBot()

def get_bot_response(message, user_email=None):
    """
    Convenient function to get bot response
    """
    return chatbot_instance.process_message(message, user_email)