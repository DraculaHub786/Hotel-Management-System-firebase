# training_data.py
import re
from datetime import datetime

# ============================================
# INTENT CLASSIFICATION WITH CONFIDENCE SCORES
# ============================================

INTENT_PATTERNS = {
    "booking_inquiry": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["book", "reserve", "reservation", "availability", "available"],
        "secondary_keywords": ["room", "stay", "check in", "want to", "need","type"],
        "negative_keywords": ["cancel", "modify", "change"],
        "variations": [
            "i want to book", "how do i book", "book a room", "make a reservation",
            "reserve a room", "are rooms available", "check availability",
            "can i book", "booking process", "want to reserve", "type of rooms"
        ]
    },
    
    "booking_modification": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["modify", "change", "update", "edit", "reschedule"],
        "secondary_keywords": ["booking", "reservation", "date", "room"],
        "variations": [
            "change my booking", "modify reservation", "update my booking",
            "reschedule my stay", "change dates", "change check-in",
            "extend my stay", "shorten my booking"
        ]
    },
    
    "cancellation_inquiry": {
        "confidence_threshold": 0.8,
        "primary_keywords": ["cancel", "cancellation", "refund"],
        "secondary_keywords": ["booking", "reservation", "policy", "money back"],
        "variations": [
            "cancel my booking", "cancellation policy", "how to cancel",
            "get a refund", "cancel reservation", "refund policy"
        ]
    },
    
    "pricing_inquiry": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["price", "cost", "rate", "charge", "expensive", "cheap"],
        "secondary_keywords": ["room", "stay", "night", "how much"],
        "variations": [
            "how much does it cost", "room prices", "what are the rates",
            "price per night", "how expensive", "cheapest room", "room rates"
        ]
    },
    
    "amenities_inquiry": {
        "confidence_threshold": 0.65,
        "primary_keywords": ["amenity", "amenities", "facility", "facilities", "feature"],
        "secondary_keywords": ["wifi", "gym", "pool", "breakfast", "parking", "spa"],
        "variations": [
            "what amenities", "do you have wifi", "is there a gym",
            "facilities available", "what's included", "hotel features"
        ]
    },
    
    "checkin_checkout": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["check in", "check out", "check-in", "check-out", "arrival", "departure"],
        "secondary_keywords": ["time", "when", "what time", "hours"],
        "variations": [
            "check in time", "check out time", "when can i check in",
            "what time is check out", "arrival time", "departure time",
            "early check in", "late check out"
        ]
    },
    
    "payment_methods": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["payment", "pay", "card", "upi", "wallet", "netbanking"],
        "secondary_keywords": ["method", "how", "accept", "options"],
        "variations": [
            "payment methods", "how to pay", "do you accept card",
            "payment options", "can i pay with upi", "accepted payments"
        ]
    },
    
    "location_transport": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["location", "address", "where", "airport", "shuttle", "transport"],
        "secondary_keywords": ["how to reach", "directions", "pickup", "drop"],
        "variations": [
            "where are you located", "hotel address", "airport shuttle",
            "how to reach", "pickup service", "transportation"
        ]
    }
}

# ============================================
# EXPANDED KNOWLEDGE BASE WITH METADATA
# ============================================

EXPANDED_KNOWLEDGE_BASE = {
    
    # ============================================
    # BOOKING & RESERVATIONS
    # ============================================
    "booking_new": {
        "intent": "booking_inquiry",
        "confidence_boost": 0.1,
        "keywords": ["book", "booking", "reserve", "reservation", "new booking", "make reservation"],
        "entities": ["room_type", "date", "guests"],
        "patterns": [
            r"(how|where) (do|can) (i|we) book",
            r"(make|create) (a )?reservation",
            r"want to (book|reserve)",
            r"(book|reserve) (a )?room",
            r"new booking",
            r"(check|see) availability",
            r"available rooms"
        ],
        "context_required": False,
        "follow_up_questions": [
            "What type of room would you like?",
            "When would you like to check in?",
            "How many guests?"
        ],
        "responses": [
            "I'd be happy to help you book a room! 😊\n\nHere's how to make a reservation:\n\n1️⃣ Click 'NEW BOOKING' in the navigation menu\n2️⃣ Select your check-in and check-out dates\n3️⃣ Choose number of guests\n4️⃣ Pick your preferred room from available options\n5️⃣ Review details and proceed to secure payment\n\nYour booking confirmation will be sent instantly to your email! 📧\n\nNeed help choosing a room? I can tell you about our room types and prices!",
            
            "Great choice staying with us! 🏨\n\nBooking is super easy:\n\n✅ Go to 'NEW BOOKING' on your dashboard\n✅ Pick your dates (Check-in: 7AM onwards, Check-out: 11PM)\n✅ Select number of guests (1-4 depending on room)\n✅ Choose from 5 room types (₹2,000 - ₹8,000/night)\n✅ Complete secure payment\n\nBonus: All bookings get instant confirmation + loyalty points! 🌟\n\nWant me to explain our room options?",
            
            "Welcome to Nur-e-Haya! Let me guide you through the booking process:\n\n📋 **Quick Booking Steps:**\n• Navigate to NEW BOOKING section\n• Enter your travel dates\n• Select guest count (1-4 persons)\n• Browse available rooms with real-time pricing\n• Add any special requests\n• Secure checkout with multiple payment options\n\n💡 **Pro Tip:** Book 48+ hours in advance for free cancellation!\n\nShould I tell you about our rooms and rates?"
        ],
        "related_intents": ["pricing_inquiry", "room_types", "availability_check"],
        "requires_authentication": False
    },

    "booking_group": {
        "intent": "booking_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["group", "multiple rooms", "bulk", "corporate", "wedding", "event", "conference", "party"],
        "entities": ["room_count", "event_type", "date_range"],
        "patterns": [
            r"(book|reserve) (multiple|several|many|\d+) rooms",
            r"group (booking|reservation)",
            r"corporate (booking|accommodation|event)",
            r"(wedding|conference|event|party) (booking|accommodation)",
            r"book for (\d+) (people|guests|persons)",
            r"bulk booking",
            r"company stay"
        ],
        "context_required": False,
        "responses": [
            "Excellent! We specialize in group bookings and events! 🎉\n\n**For 5+ rooms or special events:**\n\n📞 **Call:** +91 8010572845 (Ext: 2)\n📧 **Email:**\nsupport@nur-e-haya.com\n→ General inquiries\n→ Response within 24 hours\n\nevents@nur-e-haya.com\n→ Group bookings & events\n→ Response within 2 hours\n\ncomplaints@nur-e-haya.com\n→ Complaints & feedback\n→ Priority response\n\n💬 **Live Chat:**\n→ Available on dashboard\n→ Instant AI responses\n→ Human agent available 9 AM - 9 PM\n\n📱 **WhatsApp:**\n+91-XXXXX-XXXXX\n→ Quick queries\n→ Booking confirmations\n→ Updates & notifications\n\n🏨 **Visit Us:**\nNur-e-Haya Luxury Hotel\n[Complete Address]\n[City, State - PIN]\n\n**⏰ RESPONSE TIMES:**\n• Phone: Immediate\n• Live Chat: Instant\n• WhatsApp: Within 1 hour\n• Email: Within 24 hours\n• Complaints: Within 2 hours\n\nHow can we help you today?"
        ],
        "follow_up_questions": [
            "What would you like to inquire about?",
            "Would you prefer phone or email contact?",
            "Do you have an urgent query?"
        ],
        "related_intents": ["complaint_handling", "booking_inquiry"]
    },

    # ============================================
    # SPECIAL SITUATIONS
    # ============================================
    "pets_policy": {
        "intent": "special_requests",
        "confidence_boost": 0.15,
        "keywords": ["pet", "pets", "dog", "cat", "animal", "bring pet"],
        "entities": ["pet_type"],
        "patterns": [
            r"(can i|do you|are) (bring|allow|accept) pets",
            r"pet (policy|friendly|allowed)",
            r"(bring|have) (my |a )?(dog|cat|pet|animal)",
            r"pet accommodation"
        ],
        "context_required": False,
        "responses": [
            "Thank you for asking about our pet policy! 🐾\n\n**🏨 PET POLICY:**\n\n❌ **Regular Pets:** Unfortunately, we don't allow pets in our hotel to ensure comfort for all guests, including those with allergies or pet phobias.\n\n✅ **Service Animals:** Certified service animals (guide dogs, assistance dogs) are ALWAYS welcome with proper documentation!\n\n**🐕 WHAT WE CAN HELP WITH:**\n\n**Nearby Pet Care:**\nWe can recommend excellent facilities near our hotel:\n\n🏥 **Pet Boarding:**\n• Paws & Claws Pet Resort (2 km away)\n• Happy Tails Boarding (3 km away)\n• 24/7 supervision, AC rooms, play area\n• Rates: ₹500-800/day\n\n🏥 **Pet Daycare:**\n• DogSpot Daycare (1.5 km)\n• Hourly/daily options\n• Trained staff, vet on call\n\n🚗 **We Can Arrange:**\n• Transportation to pet facility\n• Pick-up/drop-off coordination\n• Daily updates on your pet\n\n**✅ SERVICE ANIMAL REQUIREMENTS:**\n• Valid certification/ID\n• Vaccination records\n• Must be leashed/harnessed\n• Well-behaved in public areas\n• Free of charge!\n\n**💡 ALTERNATIVES:**\n• Stay with us, board your pet nearby\n• Visit your pet daily (we'll help arrange transport)\n• Many guests do this successfully!\n\n**📞 NEED RECOMMENDATIONS?**\nCall: +91 8010572845\nOur staff can help find the best pet care option for your furry friend!\n\nWould you like contact details for nearby pet boarding facilities?"
        ],
        "follow_up_questions": [
            "Do you have a service animal?",
            "Would you like pet boarding recommendations?",
            "Need help arranging pet care?"
        ],
        "related_intents": ["special_requests", "location_transport"],
        "sensitive_topic": True
    },

    "complaint_handling": {
        "intent": "complaint",
        "confidence_boost": 0.2,
        "keywords": ["complaint", "issue", "problem", "dissatisfied", "unhappy", "not satisfied", "poor", "bad"],
        "entities": ["complaint_type", "severity"],
        "patterns": [
            r"(have|got) (a |an )?(complaint|issue|problem)",
            r"(not|un)(satisfied|happy)",
            r"(poor|bad) (service|experience|quality)",
            r"want to complain",
            r"(room|service) (not|wasn't) (good|clean|working)"
        ],
        "context_required": False,
        "responses": [
            "I'm truly sorry to hear about your experience. 😔\n\nYour satisfaction matters deeply to us, and we want to make this right immediately.\n\n**🚨 IMMEDIATE ASSISTANCE:**\n\n**For urgent issues (Room problems, safety concerns):**\n📞 **Call NOW:** +91 8010572845\n→ Press 0 for front desk\n→ Available 24/7\n→ Instant response guaranteed\n\n**For service complaints:**\n📧 **Email:** complaints@nur-e-haya.com\n→ Response within 2 hours\n→ Management reviews personally\n\n**📝 COMPLAINT PROCESS:**\n\n1️⃣ **Report Issue**\n   • Call/email with details\n   • Booking ID helpful\n   • Photo evidence (if applicable)\n\n2️⃣ **Immediate Action**\n   • Staff dispatched within 15 mins\n   • Issue resolved on priority\n   • Alternative arrangement if needed\n\n3️⃣ **Follow-up**\n   • Manager personally follows up\n   • Compensation evaluated\n   • Quality assurance review\n\n4️⃣ **Resolution**\n   • Issue fixed completely\n   • Compensation/refund if warranted\n   • Preventive measures taken\n\n**💡 WHAT WE CAN DO:**\n✓ Room change (immediate)\n✓ Service recovery\n✓ Compensation (if applicable)\n✓ Full refund (for serious issues)\n✓ Future discount\n✓ Management meeting\n\n**🎯 OUR COMMITMENT:**\n• Take every complaint seriously\n• Respond within 15 minutes\n• Resolve within 2 hours\n• Follow up post-stay\n• Continuous improvement\n\n**Please tell me:**\n1. What specific issue you're facing?\n2. Your room number/booking ID?\n3. How urgent is this?\n\nI'll escalate this to management RIGHT NOW and ensure immediate resolution.\n\nYour comfort is our priority. We'll make this right! 🙏"
        ],
        "follow_up_questions": [
            "Can you describe the issue in detail?",
            "Is this an urgent matter?",
            "What's your booking ID or room number?",
            "Would you like to speak with a manager?"
        ],
        "related_intents": ["refund_request", "room_change"],
        "escalation_required": True,
        "management_alert": True
    },

    # ============================================
    # CONVERSATIONAL RESPONSES
    # ============================================
    "greeting_general": {
        "intent": "greeting",
        "confidence_boost": 0.05,
        "keywords": ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"],
        "patterns": [
            r"^(hi|hello|hey|hola|namaste)[\s!.]*$",
            r"good (morning|afternoon|evening|day)",
        ],
        "context_required": False,
        "responses": [
            "Hello! Welcome to Nur-e-Haya! 👋\n\nI'm your AI assistant, here to help 24/7 with:\n✓ Booking rooms\n✓ Answering questions about our hotel\n✓ Check-in/check-out information\n✓ Policies and pricing\n✓ Special requests\n\nHow can I assist you today?",
            
            "Hi there! 😊 Great to have you here!\n\nI can help you with:\n• Room reservations\n• Pricing information\n• Hotel amenities\n• Cancellation policies\n• Any other questions!\n\nWhat would you like to know?",
            
            "Hey! Welcome to Nur-e-Haya Luxury Hotel! 🏨\n\nI'm here to make your booking experience smooth and easy!\n\nPopular questions I can answer:\n→ How do I book a room?\n→ What are your room rates?\n→ What's the cancellation policy?\n→ What amenities do you offer?\n\nWhat brings you here today?"
        ],
        "follow_up_questions": [
            "Are you looking to make a booking?",
            "Do you have questions about our hotel?",
            "Need help with an existing reservation?"
        ],
        "related_intents": ["booking_inquiry", "room_types"]
    },

    "gratitude_response": {
        "intent": "gratitude",
        "confidence_boost": 0.1,
        "keywords": ["thank", "thanks", "appreciate", "grateful", "thank you"],
        "patterns": [
            r"thank(s| you)",
            r"appreciate (it|this|your help)",
            r"(that's|that is|this is) (helpful|great|perfect|wonderful)",
            r"grateful",
            r"you('re| are) (great|awesome|helpful)"
        ],
        "context_required": False,
        "responses": [
            "You're very welcome! 😊\n\nHappy to help! Is there anything else you'd like to know about Nur-e-Haya?\n\nI'm here 24/7 for:\n• Booking assistance\n• Policy questions\n• Special requests\n• General inquiries\n\nFeel free to ask anytime!",
            
            "My pleasure! 🌟\n\nGlad I could assist you! Don't hesitate to reach out if you have more questions.\n\n💡 Quick tip: You can ask me about:\n→ Room availability\n→ Pricing & discounts\n→ Amenities & services\n→ Booking modifications\n→ Anything else!\n\nWhat else can I help with?",
            
            "You're most welcome! 🎉\n\nIt's always a pleasure to help our guests!\n\nRemember:\n✓ I'm available 24/7\n✓ No question is too small\n✓ I can help with bookings, policies, and more!\n\nAnything else you need?"
        ],
        "engagement_continuation": True
    },

    "farewell": {
        "intent": "farewell",
        "confidence_boost": 0.1,
        "keywords": ["bye", "goodbye", "see you", "later", "that's all"],
        "patterns": [
            r"(bye|goodbye|see you|gtg|gotta go)",
            r"that('s| is) all",
            r"(nothing|no) (else|more)",
            r"thanks? bye"
        ],
        "context_required": False,
        "responses": [
            "Goodbye! Have a wonderful day! 👋\n\nWe look forward to hosting you at Nur-e-Haya! If you need anything later, I'm always here to help.\n\nHave a great time! 🌟",
            
            "Thank you for chatting with me! 😊\n\nIf you need anything else, just come back - I'm available 24/7!\n\nLooking forward to welcoming you to Nur-e-Haya! Safe travels! ✨",
            
            "Take care! Have an amazing day! 🎉\n\nRemember, I'm here anytime you need:\n• Booking help\n• Information\n• Support\n\nCan't wait to host you at Nur-e-Haya! 🏨"
        ]
    },

    "confusion_help": {
        "intent": "unclear",
        "confidence_boost": 0,
        "keywords": ["what", "huh", "don't understand", "confused", "unclear"],
        "patterns": [
            r"^(what|huh|\?+)$",
            r"(don't|do not|didn't) understand",
            r"(not clear|unclear|confus(ed|ing))",
            r"can you (explain|clarify|elaborate)",
            r"(say|tell) (that )?again"
        ],
        "context_required": True,
        "responses": [
            "I apologize for any confusion! Let me help you better. 😊\n\n**📚 I can assist with:**\n\n1️⃣ **Bookings**\n• How to reserve rooms\n• Check availability\n• Modify/cancel bookings\n\n2️⃣ **Room Information**\n• Types & prices\n• Amenities included\n• Capacity & features\n\n3️⃣ **Policies**\n• Check-in/check-out times\n• Cancellation policy\n• Refund process\n\n4️⃣ **Services**\n• Payment methods\n• Airport shuttle\n• Dining options\n\n5️⃣ **Contact**\n• Phone numbers\n• Email addresses\n• Emergency support\n\n**💬 Try asking:**\n• \"How do I book a room?\"\n• \"What are your room rates?\"\n• \"What's the cancellation policy?\"\n• \"Do you have airport shuttle?\"\n• \"What payment methods do you accept?\"\n\nWhat specific information would you like to know?"
        ],
        "provides_examples": True
    },

    # ============================================
    # PROMO & OFFERS
    # ============================================
    "promo_codes": {
        "intent": "pricing_inquiry",
        "confidence_boost": 0.1,
        "keywords": ["promo", "discount", "coupon", "offer", "code", "deal"],
        "entities": ["promo_code"],
        "patterns": [
            r"(promo|discount|coupon) code",
            r"(any|current|available) (offer|discount|deal|promotion)",
            r"how to get discount",
            r"(special|seasonal) offer"
        ],
        "context_required": False,
        "responses": [
            "Great! We have active discount codes! 🎉\n\n**💰 CURRENT PROMO CODES:**\n\n**🎁 WELCOME10**\n• 10% OFF on first booking\n• Valid for all room types\n• New users only\n• No minimum booking\n• Code: **WELCOME10**\n\n**💵 SAVE500**\n• Flat ₹500 OFF\n• Valid on bookings ₹4,000+\n• All room types\n• All users\n• Code: **SAVE500**\n\n**🌟 LUXURY20**\n• 20% OFF on Luxury rooms only\n• Valid on bookings 3+ nights\n• Limited period offer\n• Code: **LUXURY20**\n\n**👨‍👩‍👧‍👦 FAMILY15**\n• 15% OFF on Family rooms\n• Valid on bookings 5+ nights\n• Perfect for vacations\n• Code: **FAMILY15**\n\n**💝 WEEKEND25**\n• 25% OFF on weekend bookings\n• Friday-Sunday only\n• Double/Suite rooms\n• Code: **WEEKEND25**\n\n**📅 SEASONAL OFFERS:**\n• Summer Sale: Up to 30% off (Jun-Aug)\n• Festival Special: 20% off (During festivals)\n• Year-End Sale: 25% off (Dec 20-31)\n\n**🎯 HOW TO USE:**\n1. Select your room\n2. Proceed to payment\n3. Enter promo code\n4. Click 'Apply'\n5. Discount applied automatically!\n\n**💡 STACKING RULES:**\n• Only one code per booking\n• Cannot combine with other offers\n• Loyalty discounts stack with promo codes!\n\n**📧 EXCLUSIVE OFFERS:**\nSubscribe to our newsletter for:\n• Early access to sales\n• Exclusive discount codes\n• Birthday special offers\n• Member-only deals\n\n**🎊 BULK BOOKING DISCOUNT:**\n• 5-10 rooms: 10% OFF\n• 11-20 rooms: 15% OFF\n• 20+ rooms: 25% OFF\n• Contact: events@nur-e-haya.com\n\n**Valid Till:** Check individual code validity\n**T&C:** Standard cancellation policy applies\n\nWhich code would you like to use?"
        ],
        "follow_up_questions": [
            "Which promo code interests you?",
            "Ready to book with discount?",
            "Want to subscribe for exclusive offers?",
            "Need help applying the code?"
        ],
        "related_intents": ["pricing_details", "booking_inquiry"],
        "conversion_driver": True
    },

    # ============================================
    # OWNER & BUSINESS INFORMATION
    # ============================================

    "owner_info": {
        "intent": "business_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["owner", "who owns", "proprietor", "management", "founder", "ceo", "director", "manager"],
        "entities": ["contact_type"],
        "patterns": [
            r"who (is|owns|runs|manages|own)",
            r"(owner|proprietor|founder|ceo|director|management) (of|details|info|contact)",
            r"(who|about) (the )?(hotel )?(owner|management)",
            r"owned by",
            r"contact (owner|management)",
            r"speak to (owner|proprietor|management)"
        ],
        "context_required": False,
        "responses": [
            "**🏨 ABOUT NUR-E-HAYA LUXURY HOTEL**\n\n**👤 OWNER/PROPRIETOR:**\n[Afjal Ansari]\nFounder & Managing Director\n\n**📧 CONTACT DETAILS:**\n\n**Primary Email:**\nowner@nur-e-haya.com\n→ Direct owner communication\n→ Response within 24-48 hours\n\n**Business Email:**\nsupport@nur-e-haya.com\n→ General inquiries\n→ Response within 24 hours\n\n**Phone:**\n📞 +91 8010572845\n→ Main reception (24/7)\n→ Press Ext: 1 for management\n\n**Mobile (Owner):**\n📱 +91 8010572845\n→ Business hours: 9 AM - 6 PM\n→ For urgent business matters only\n\n**📍 OFFICE ADDRESS:**\nNur-e-Haya Luxury Hotel\n[Complete Street Address]\n[City, State - PIN Code]\n[Country]\n\n**🕐 OFFICE HOURS:**\nMonday - Saturday: 9:00 AM - 6:00 PM\nSunday: Closed (Emergency contact available)\n\n**💼 BUSINESS DETAILS:**\n\n**Established:** [Year]\n**Business Type:** Luxury Hospitality\n**Services:** Hotel Accommodation, Events, Corporate Bookings\n**Capacity:** [Number] Rooms\n**Rating:** ⭐⭐⭐⭐⭐ (4.8/5)\n\n**🏆 CERTIFICATIONS:**\n✓ Licensed Hospitality Provider\n✓ ISO 9001:2015 Certified\n✓ Tourism Board Approved\n✓ Safety & Hygiene Certified\n\n**📱 SOCIAL MEDIA:**\nFacebook: facebook.com/nur-e-haya\nInstagram: @nurehayadirectory\nLinkedIn: linkedin.com/company/nur-e-haya\nTwitter: @nurehayadirectory\n\n**🌐 WEBSITE:**\nwww.nur-e-haya.com\n\n**📋 FOR BUSINESS INQUIRIES:**\n• Partnerships: partnerships@nur-e-haya.com\n• Corporate Bookings: corporate@nur-e-haya.com\n• Events: events@nur-e-haya.com\n• Media: media@nur-e-haya.com\n\n**💡 ABOUT THE OWNER:**\n[Afjal Ansari] founded Nur-e-Haya with a vision to provide world-class hospitality with personalized service. With [X years] of experience in the hospitality industry, [he/she] has built Nur-e-Haya into one of the region's premier luxury hotels.\n\n**🎯 OUR MISSION:**\n\"To provide exceptional hospitality experiences that exceed guest expectations through personalized service, luxury amenities, and unwavering commitment to quality.\"\n\n**👥 MANAGEMENT TEAM:**\n• General Manager: [Name]\n• Operations Head: [Name]\n• Guest Relations Manager: [Name]\n• Events Coordinator: [Name]\n\nWould you like to schedule a meeting or need specific contact information?"
        ],
        "follow_up_questions": [
            "Would you like the owner's direct email?",
            "Do you need business partnership information?",
            "Are you interested in corporate bookings?",
            "Would you like to schedule a meeting with management?"
        ],
        "related_intents": ["contact_inquiry", "business_partnership", "corporate_booking"],
        "provides_contact": True
    },

    "business_introduction": {
        "intent": "about_hotel",
        "confidence_boost": 0.12,
        "keywords": ["about", "introduction", "tell me about", "what is", "info", "information", "hotel info"],
        "entities": [],
        "patterns": [
            r"(tell|about) (me )?(about|your|the) (hotel|business|company)",
            r"what is (this|the|your) (hotel|business)",
            r"(hotel|business) (info|information|details|introduction)",
            r"who are you",
            r"introduce (yourself|the hotel)"
        ],
        "context_required": False,
        "responses": [
            "**🏨 WELCOME TO NUR-E-HAYA LUXURY HOTEL! ✨**\n\n**WHO WE ARE:**\nNur-e-Haya is a premier luxury hotel established in [Year], committed to providing exceptional hospitality experiences with personalized service and world-class amenities.\n\n**👤 FOUNDED BY:**\n[Afjal Ansari] - Founder & Managing Director\nWith [X years] of hospitality expertise\n\n**🎯 OUR VISION:**\n\"To be the most preferred luxury hotel destination, known for unparalleled guest experiences and sustainable hospitality practices.\"\n\n**⭐ WHAT MAKES US SPECIAL:**\n✨ **5 Luxury Room Categories** (₹2,000 - ₹8,000/night)\n✨ **World-Class Amenities** (WiFi, Gym, Pool, Spa, Restaurant)\n✨ **24/7 Guest Services** (Room service, Concierge, Support)\n✨ **Prime Location** (Near airport, business district, attractions)\n✨ **Event Facilities** (Weddings, Conferences, Corporate events)\n✨ **Flexible Policies** (Free cancellation 48hrs+, Easy modifications)\n\n**📊 OUR NUMBERS:**\n• [Number] Luxury Rooms\n• 4.8⭐ Average Rating\n• [Number]+ Happy Guests Annually\n• 24/7 Service Availability\n• 100+ Staff Members\n\n**🏆 ACHIEVEMENTS:**\n✓ Best Luxury Hotel [Year/Region]\n✓ Excellence in Hospitality Award\n✓ Traveler's Choice Award\n✓ ISO 9001:2015 Certified\n✓ Tourism Board Gold Certification\n\n**📍 LOCATION:**\nNur-e-Haya Luxury Hotel\n[Complete Address]\n[City, State - PIN]\n\n**📞 CONTACT INFORMATION:**\n• Phone: +91 8010572845 (24/7)\n• Email: support@nur-e-haya.com\n• Owner: owner@nur-e-haya.com\n• Website: www.nur-e-haya.com\n\n**💼 BUSINESS SERVICES:**\n• Individual Bookings\n• Corporate Accommodations\n• Group Bookings (5+ rooms)\n• Event Management\n• Wedding Packages\n• Conference Facilities\n\n**🌱 OUR COMMITMENT:**\n• Eco-friendly operations\n• Sustainable practices\n• Community engagement\n• Guest safety & security\n• Continuous improvement\n\n**👥 MEET OUR LEADERSHIP:**\n• Founder & MD: [Afjal Ansari]\n• General Manager: [Name]\n• Operations Head: [Name]\n• Guest Relations: [Name]\n\nWould you like to know more about our rooms, services, or make a booking?"
        ],
        "follow_up_questions": [
            "What would you like to know more about?",
            "Are you interested in booking a room?",
            "Need information about specific services?",
            "Would you like to contact our owner/management?"
        ],
        "related_intents": ["owner_info", "contact_inquiry", "room_types", "amenities_inquiry"]
    },

    "contact_inquiry": {
        "intent": "contact_request",
        "confidence_boost": 0.15,
        "keywords": ["contact", "reach", "call", "email", "phone", "number", "address", "get in touch"],
        "entities": ["contact_type", "urgency"],
        "patterns": [
            r"(how|where) (can|do) (i|we) (contact|reach|call)",
            r"contact (details|info|information|number)",
            r"(phone|email|address) (number|details)",
            r"(get|how to) (in touch|contact)",
            r"reach (you|hotel|owner|management)",
            r"call (you|hotel)"
        ],
        "context_required": False,
        "responses": [
            "**📞 COMPLETE CONTACT INFORMATION**\n\n**🏨 MAIN RECEPTION (24/7):**\n📞 **Phone:** +91 8010572845\n→ Press 0: Reception/Front Desk\n→ Press 1: Management\n→ Press 2: Events & Group Bookings\n→ Press 3: Complaints & Feedback\n\n**📧 EMAIL ADDRESSES:**\n\n**General Inquiries:**\nsupport@nur-e-haya.com\n→ Bookings, questions, support\n→ Response: Within 24 hours\n\n**Owner/Management:**\nowner@nur-e-haya.com\n→ Direct communication with owner\n→ Business partnerships, feedback\n→ Response: Within 24-48 hours\n\n**Events & Group Bookings:**\nevents@nur-e-haya.com\n→ Weddings, conferences, corporate\n→ Response: Within 2 hours\n\n**Complaints & Urgent Issues:**\ncomplaints@nur-e-haya.com\n→ Service issues, urgent matters\n→ Response: Within 2 hours\n→ Management reviews personally\n\n**Corporate Bookings:**\ncorporate@nur-e-haya.com\n→ Business travelers, companies\n→ Bulk booking discounts\n\n**Media & Press:**\nmedia@nur-e-haya.com\n→ Press inquiries, collaborations\n\n**📱 WHATSAPP SUPPORT:**\n+91-[WhatsApp Number]\n→ Quick queries\n→ Booking confirmations\n→ Updates & notifications\n→ Response: Within 1 hour\n\n**💬 LIVE CHAT:**\n→ Available on website/dashboard\n→ AI chatbot: 24/7 instant responses\n→ Human agent: 9 AM - 9 PM daily\n\n**📍 PHYSICAL ADDRESS:**\nNur-e-Haya Luxury Hotel\n[Complete Street Address]\n[Area/Locality]\n[City, State - PIN Code]\n[Country]\n\n**🗺️ GOOGLE MAPS:**\n[Link: maps.google.com/nur-e-haya]\n→ Click for directions\n\n**🕐 OFFICE HOURS:**\n**Management Office:**\nMonday - Saturday: 9:00 AM - 6:00 PM\nSunday: Closed (Emergency: +91-XXXXX-XXXXX)\n\n**Reception (24/7):**\nAlways open, all days\n\n**📱 SOCIAL MEDIA:**\n• Facebook: facebook.com/nur-e-haya\n• Instagram: @nurehayadirectory\n• Twitter: @nurehayadirectory\n• LinkedIn: linkedin.com/company/nur-e-haya\n\n**⏰ RESPONSE TIMES:**\n• Phone: Immediate (24/7)\n• WhatsApp: Within 1 hour\n• Live Chat: Instant (AI) / 9AM-9PM (Human)\n• Email (General): Within 24 hours\n• Email (Complaints): Within 2 hours\n• Email (Owner): Within 24-48 hours\n\n**🚨 EMERGENCY CONTACT:**\nFor urgent issues (safety, medical, security):\n📞 +91 8010572845 (Press 0)\nAvailable 24/7, immediate response\n\n**💼 BUSINESS INQUIRIES:**\n**Partnerships:** partnerships@nur-e-haya.com\n**Collaborations:** +91-[Business Mobile]\n**Owner Direct:** owner@nur-e-haya.com\n\nWhat would you like to inquire about?"
        ],
        "follow_up_questions": [
            "What would you like to contact us about?",
            "Do you prefer phone or email?",
            "Is this an urgent matter?",
            "Would you like to speak with management?"
        ],
        "related_intents": ["owner_info", "complaint_handling", "booking_inquiry"],
        "provides_contact": True
    },

    "business_partnership": {
        "intent": "partnership_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["partnership", "collaborate", "collaboration", "business deal", "tie up", "corporate", "vendor"],
        "entities": ["partnership_type"],
        "patterns": [
            r"(business )?(partnership|collaboration|tie.?up)",
            r"(want to|interested in) (partner|collaborate|work with)",
            r"(corporate|business) (deal|opportunity|proposal)",
            r"(become|be) (a )?(vendor|partner|supplier)",
            r"(work|business) (with|together)"
        ],
        "context_required": False,
        "responses": [
            "**🤝 BUSINESS PARTNERSHIPS & COLLABORATIONS**\n\nThank you for your interest in partnering with Nur-e-Haya! We're always open to mutually beneficial collaborations.\n\n**💼 PARTNERSHIP OPPORTUNITIES:**\n\n**1️⃣ Corporate Tie-ups:**\n• Employee accommodation programs\n• Discounted corporate rates\n• Dedicated account manager\n• Flexible payment terms\n• Priority booking\n\n**2️⃣ Travel & Tourism:**\n• Travel agency partnerships\n• Tour operator collaborations\n• Commission-based programs\n• Exclusive rates for groups\n\n**3️⃣ Vendor & Suppliers:**\n• Food & beverage suppliers\n• Laundry services\n• Maintenance vendors\n• Technology partners\n• Décor & furnishing\n\n**4️⃣ Event Collaborations:**\n• Wedding planners\n• Event management companies\n• Catering services\n• Entertainment vendors\n\n**5️⃣ Digital Partnerships:**\n• OTA (Online Travel Agency) listings\n• Booking platform integrations\n• Marketing collaborations\n• Technology solutions\n\n**📧 CONTACT FOR PARTNERSHIPS:**\n\n**Primary Contact:**\npartnerships@nur-e-haya.com\n→ All partnership inquiries\n→ Response within 24 hours\n\n**Owner/Management:**\nowner@nur-e-haya.com\n📞 +91-[Owner Mobile]\n→ Strategic partnerships\n→ Major collaborations\n\n**Corporate Bookings:**\ncorporate@nur-e-haya.com\n→ Company tie-ups\n→ Bulk booking arrangements\n\n**📋 PARTNERSHIP PROCESS:**\n\n1️⃣ **Initial Contact**\n   → Send inquiry via email\n   → Include business details & proposal\n   → Mention partnership type\n\n2️⃣ **Evaluation**\n   → Our team reviews proposal\n   → Response within 24-48 hours\n   → Request for additional info if needed\n\n3️⃣ **Meeting**\n   → Schedule in-person/virtual meeting\n   → Discuss terms & conditions\n   → Present mutual benefits\n\n4️⃣ **Agreement**\n   → Draft partnership agreement\n   → Legal review\n   → Sign MOU/Contract\n\n5️⃣ **Onboarding**\n   → Setup processes\n   → Training (if required)\n   → Launch collaboration\n\n**📄 INFORMATION NEEDED:**\nPlease include in your inquiry:\n✓ Company name & registration details\n✓ Nature of business\n✓ Partnership proposal summary\n✓ Expected benefits (both sides)\n✓ Contact person details\n✓ Supporting documents (if any)\n\n**💡 WHAT WE OFFER PARTNERS:**\n• Competitive rates/commissions\n• Dedicated support\n• Marketing collaboration\n• Flexible terms\n• Long-term relationships\n• Transparent dealings\n\n**🎯 CURRENT PARTNERS:**\nWe proudly work with [X] corporate partners, [Y] travel agencies, and [Z] local businesses.\n\n**📞 SCHEDULE A MEETING:**\nContact us to arrange a meeting with our management:\n\n**Owner:** [Afjal Ansari]\n📧 owner@nur-e-haya.com\n📞 +91-[Owner Mobile]\n\n**Business Development:**\n📧 partnerships@nur-e-haya.com\n📞 +91 8010572845 (Ext: 1)\n\nLooking forward to potential collaboration! 🌟"
        ],
        "follow_up_questions": [
            "What type of partnership are you interested in?",
            "Can you tell us about your business?",
            "Would you like to schedule a meeting?",
            "Do you have a partnership proposal ready?"
        ],
        "related_intents": ["owner_info", "contact_inquiry", "corporate_booking"],
        "requires_escalation": True
    },
        "owner_inquiry": {
            "confidence_threshold": 0.75,
            "primary_keywords": ["owner", "proprietor", "founder", "ceo", "director", "management"],
            "secondary_keywords": ["who", "contact", "name", "email", "phone", "about"],
            "variations": [
                "who is the owner", "who owns this hotel", "owner details",
                "contact owner", "owner email", "owner phone number",
                "speak to owner", "meet the owner", "about the owner"
            ]
        },
        
        "about_hotel": {
            "confidence_threshold": 0.70,
            "primary_keywords": ["about", "information", "introduce", "tell me about", "what is"],
            "secondary_keywords": ["hotel", "business", "company", "you", "this"],
            "variations": [
                "tell me about the hotel", "what is this hotel", "hotel information",
                "about your hotel", "introduce yourself", "who are you",
                "hotel info", "about this business"
            ]
        },
        
        "contact_general": {
            "confidence_threshold": 0.75,
            "primary_keywords": ["contact", "reach", "call", "email", "phone", "address"],
            "secondary_keywords": ["how", "number", "details", "information", "get in touch"],
            "variations": [
                "contact details", "how to contact", "phone number", "email address",
                "how to reach you", "contact information", "get in touch"
            ]
        },
        
        "partnership_inquiry": {
            "confidence_threshold": 0.75,
            "primary_keywords": ["partnership", "collaborate", "collaboration", "business deal", "tie up"],
            "secondary_keywords": ["corporate", "vendor", "supplier", "work with", "business"],
            "variations": [
                "business partnership", "want to collaborate", "corporate tie up",
                "become a partner", "business opportunity", "work together"
            ]
        },
    "room_facilities": {
        "intent": "amenities_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["toilet", "bathroom", "washroom", "bath", "shower", "basin", "sink", "towel", "toiletries", "soap", "shampoo"],
        "entities": ["facility_type"],
        "patterns": [
            r"(do you have|is there) (a )?(toilet|bathroom|washroom)",
            r"(attached|private) (bathroom|toilet|washroom)",
            r"bath(room)? facilities",
            r"wash(room)? available",
            r"(shower|bath tub|bathtub)",
            r"(towels|toiletries|soap|shampoo)"
        ],
        "context_required": False,
        "responses": [
            "**🚿 BATHROOM FACILITIES**\n\nAll our rooms include:\n\n**✅ Private Attached Bathroom:**\n• Modern western-style toilet\n• Hot & cold shower (24/7)\n• Wash basin with mirror\n• Bathtub (Suite & Luxury rooms only)\n\n**🧴 Complimentary Toiletries:**\n• Premium soap & shampoo\n• Conditioner\n• Body wash\n• Dental kit\n• Shaving kit\n• Fresh towels (bath + hand)\n• Bathrobes (Luxury rooms)\n\n**💧 Additional Features:**\n• Hair dryer\n• Exhaust fan\n• Anti-slip flooring\n• 24/7 hot water\n• Geyser in every bathroom\n\n**🔧 Daily Housekeeping:**\n• Fresh towels daily\n• Toiletries refilled\n• Deep cleaning\n\nNeed extra towels or toiletries? Just call room service!",
            
            "**🛁 COMPLETE BATHROOM AMENITIES**\n\nEvery room at Nur-e-Haya features:\n\n**Private Bathroom:**\n✓ Attached western toilet\n✓ Hot/cold shower system\n✓ Wash basin with large mirror\n✓ Bathtub (in Suite/Luxury)\n✓ Exhaust ventilation\n\n**Free Toiletries Provided:**\n✓ Eco-friendly soap\n✓ Shampoo & conditioner\n✓ Body lotion\n✓ Toothbrush & paste\n✓ Razor & shaving cream\n✓ Cotton buds\n\n**Bathroom Linen:**\n✓ 2 Bath towels per guest\n✓ Hand towels\n✓ Floor mat\n✓ Bathrobe (Luxury only)\n\n**Utilities:**\n✓ Hair dryer available\n✓ 24/7 hot water\n✓ Water heater/geyser\n✓ Power outlet for charging\n\n**Cleanliness:**\n✓ Sanitized before check-in\n✓ Daily cleaning service\n✓ Fresh linens daily\n\nAll bathrooms meet international hygiene standards!",
            
            "**🚽 BATHROOM & HYGIENE FACILITIES**\n\n**What's Included:**\n\n🚿 **Shower Area:**\n• Adjustable hot/cold mixer\n• Rain shower head\n• Handheld spray\n• Glass partition\n• Anti-slip mat\n\n🚽 **Toilet:**\n• Modern western commode\n• Jet spray/bidet\n• Toilet paper holder\n• Flush system\n• Exhaust fan\n\n🪞 **Vanity Area:**\n• Large wall mirror\n• Wash basin\n• Counter space\n• Storage cabinet\n• Power socket\n\n🧴 **Toiletries Kit:**\n• Herbal soap bar\n• Shampoo sachets\n• Conditioner\n• Body wash\n• Moisturizer\n• Dental kit\n• Shaving kit\n• Shower cap\n• Comb\n\n🛁 **Premium Features** (Suite/Luxury):\n• Jacuzzi bathtub\n• Premium toiletries\n• Bathrobes & slippers\n• Scale\n\n**📞 Need Anything Extra?**\nCall housekeeping for:\n• Extra towels\n• More toiletries\n• Bathroom cleaning\n• Special requests\n\nYour comfort is our priority!"
        ],
        "follow_up_questions": [
            "Would you like to know about other room amenities?",
            "Interested in booking a room?",
            "Any other questions about our facilities?"
        ],
        "related_intents": ["room_types", "amenities_inquiry"]
    },

    "bed_bedding": {
        "intent": "amenities_inquiry",
        "confidence_boost": 0.12,
        "keywords": ["bed", "mattress", "pillow", "blanket", "sheet", "bedding", "linen", "comfortable", "sleep"],
        "entities": ["bed_type"],
        "patterns": [
            r"(what|which) (type of|kind of)? bed",
            r"bed (size|type|comfort)",
            r"(mattress|pillow) (type|quality)",
            r"(bed )?linen",
            r"(comfortable|soft) bed",
            r"extra (pillow|blanket|sheet)"
        ],
        "context_required": False,
        "responses": [
            "**🛏️ BEDDING & COMFORT**\n\n**Bed Types by Room:**\n\n**Single Room:**\n• Queen-sized bed (5ft × 6.5ft)\n• Premium spring mattress\n• Sleeps 1 comfortably\n\n**Double Room:**\n• King-sized bed (6ft × 6.5ft)\n• Memory foam mattress\n• Sleeps 2 comfortably\n\n**Suite:**\n• King bed + Single sofa bed\n• Orthopaedic mattress\n• Sleeps 3 comfortably\n\n**Family Room:**\n• 2 Double beds (4ft each)\n• Standard spring mattress\n• Sleeps 4 comfortably\n\n**Luxury Room:**\n• California King (7ft × 7ft)\n• Premium memory foam\n• Luxury pillow-top mattress\n• Sleeps 4 comfortably\n\n**🛌 Bedding Provided:**\n✓ Egyptian cotton sheets (300 thread count)\n✓ 2 Pillows per guest (soft + firm options)\n✓ Down comforter/duvet\n✓ Blanket (winter)\n✓ Bed runner\n✓ Decorative cushions\n\n**💤 Sleep Comfort:**\n✓ Blackout curtains\n✓ Soundproof windows\n✓ AC with temperature control\n✓ Extra pillows/blankets on request\n\n**📞 Need More Bedding?**\nCall housekeeping for:\n• Extra pillows\n• Additional blankets\n• Hypoallergenic bedding\n• Bed configuration changes\n\nSweet dreams guaranteed! 😴",
            
            "**🛏️ PREMIUM BEDDING DETAILS**\n\n**Mattress Quality:**\n• All rooms: Medical-grade orthopedic mattresses\n• Luxury/Suite: Memory foam with cooling gel\n• Firm yet comfortable support\n• Hypoallergenic materials\n• Anti-dust mite covers\n\n**Pillow Selection:**\n• Standard: 2 pillows per person\n• Options: Soft, medium, firm\n• Memory foam pillows available\n• Hypoallergenic filling\n• Extra pillows: Free on request\n\n**Bed Linen:**\n• 100% Egyptian cotton sheets\n• 300+ thread count\n• Changed daily\n• Crisp white hotel-grade\n• Ironed & sanitized\n\n**Comfort Layers:**\n• Mattress protector\n• Fitted bed sheet\n• Flat top sheet\n• Duvet with cover\n• Bed throw/runner\n• Decorative pillows\n\n**Blankets:**\n• Light summer blanket\n• Heavy winter comforter\n• Both available year-round\n• Extra blankets in closet\n\n**Special Requests:**\n✓ Foam mattress topper\n✓ Body pillows\n✓ Baby crib with bedding\n✓ Extra-long sheets\n✓ Silk pillowcases\n\nJust ask our housekeeping team!"
        ],
        "follow_up_questions": [
            "Would you like to know about room types?",
            "Need information about pillows or mattresses?",
            "Ready to book your comfortable stay?"
        ],
        "related_intents": ["room_types", "special_requests"]
    },

    "water_supply": {
        "intent": "amenities_inquiry",
        "confidence_boost": 0.12,
        "keywords": ["water", "hot water", "cold water", "drinking water", "geyser", "heater", "tap"],
        "entities": [],
        "patterns": [
            r"(hot|cold|drinking) water",
            r"water (supply|available|availability)",
            r"(is there|do you have) (a )?geyser",
            r"24[/-]?7 water",
            r"water heater"
        ],
        "context_required": False,
        "responses": [
            "**💧 WATER FACILITIES**\n\n**Hot Water:**\n✓ Available 24/7 in all rooms\n✓ Electric geyser/water heater in every bathroom\n✓ Instant hot water within 2 minutes\n✓ Temperature adjustable\n\n**Cold Water:**\n✓ 24/7 municipal + backup supply\n✓ RO filtered water for drinking\n✓ Pressure-controlled taps\n\n**Drinking Water:**\n✓ 2 complimentary bottles daily (1L each)\n✓ Water dispenser in corridors\n✓ RO purified & safe\n✓ Extra bottles on request (free)\n\n**Bathroom Water:**\n✓ Hot/cold mixer taps\n✓ Rain shower with heater\n✓ Consistent water pressure\n✓ No water shortage guaranteed\n\n**Emergency Backup:**\n✓ Underground water tanks\n✓ Overhead storage tanks\n✓ Generator backup for geysers\n\nNever worry about water supply at Nur-e-Haya!",
            
            "**🚰 COMPLETE WATER AMENITIES**\n\n**Hot Water System:**\n• Electric geyser in every room\n• 24/7 availability\n• Heats in 2-3 minutes\n• Adjustable temperature (up to 60°C)\n• No timing restrictions\n\n**Cold Water:**\n• 24/7 running water\n• Municipal + borewell backup\n• Multi-stage filtration\n• Clean & safe for all uses\n\n**Drinking Water:**\n• 2 sealed bottles daily (complimentary)\n• RO purified drinking water\n• Water cooler on each floor\n• Hot water kettle in room\n• Unlimited refills\n\n**Water Quality:**\n• Regular testing\n• TDS controlled\n• Chemical-free\n• Safe for sensitive skin\n\n**No Shortage Policy:**\n• Underground reservoir (50,000L)\n• Overhead tanks per floor\n• 3-day backup supply\n• Generator for pumps\n\nYour hydration is always assured!"
        ],
        "follow_up_questions": [
            "Any other facilities you'd like to know about?",
            "Would you like to book a room?",
            "Questions about other amenities?"
        ],
        "related_intents": ["amenities_inquiry", "room_types"]
    },
    }


# ============================================
# ENTITY EXTRACTION PATTERNS
# ============================================

ENTITY_PATTERNS = {
    "date": [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}",
        r"\d{1,2} (jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        r"(today|tomorrow|next week|next month)"
    ],
    
    "guest_count": [
        r"(\d+) (guest|guests|people|person|persons|pax)",
        r"for (\d+)",
        r"(\d+) of us"
    ],
    
    "room_type": [
        r"(single|double|suite|luxury|family) room",
        r"(standard|deluxe|premium) (room|accommodation)"
    ],
    
    "phone_number": [
        r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        r"\d{10}"
    ],
    
    "email": [
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ],
    
    "price_range": [
        r"(under|below|less than|up to) ₹?\d+",
        r"₹?\d+\s*-\s*₹?\d+",
        r"(around|about|approximately) ₹?\d+"
    ],
    
    "duration": [
        r"(\d+) (night|nights|day|days)",
        r"for (\d+) (night|nights|day|days)",
        r"(\d+)n/(\d+)d"
    ],

    "owner_inquiry": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["owner", "proprietor", "founder", "ceo", "director", "management"],
        "secondary_keywords": ["who", "contact", "name", "email", "phone", "about"],
        "variations": [
            "who is the owner", "who owns this hotel", "owner details",
            "contact owner", "owner email", "owner phone number",
            "speak to owner", "meet the owner", "about the owner"
        ]
    },
    
    "about_hotel": {
        "confidence_threshold": 0.70,
        "primary_keywords": ["about", "information", "introduce", "tell me about", "what is"],
        "secondary_keywords": ["hotel", "business", "company", "you", "this"],
        "variations": [
            "tell me about the hotel", "what is this hotel", "hotel information",
            "about your hotel", "introduce yourself", "who are you",
            "hotel info", "about this business"
        ]
    },
    
    "contact_general": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["contact", "reach", "call", "email", "phone", "address"],
        "secondary_keywords": ["how", "number", "details", "information", "get in touch"],
        "variations": [
            "contact details", "how to contact", "phone number", "email address",
            "how to reach you", "contact information", "get in touch"
        ]
    },
    
    "partnership_inquiry": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["partnership", "collaborate", "collaboration", "business deal", "tie up"],
        "secondary_keywords": ["corporate", "vendor", "supplier", "work with", "business"],
        "variations": [
            "business partnership", "want to collaborate", "corporate tie up",
            "become a partner", "business opportunity", "work together"
        ]
    }
}


# ============================================
# CONTEXT MANAGEMENT
# ============================================

CONTEXT_RULES = {
    "booking_flow": {
        "sequence": ["dates", "guests", "room_type", "special_requests", "payment"],
        "required": ["dates", "guests", "room_type"],
        "optional": ["special_requests"],
        "completion_trigger": "payment"
    },
    
    "complaint_flow": {
        "sequence": ["issue_description", "severity", "urgency", "resolution_preference"],
        "required": ["issue_description"],
        "escalation_keywords": ["manager", "refund", "serious", "unacceptable", "immediately"],
        "priority_trigger": ["urgent", "emergency", "critical", "safety"]
    },
    
    "modification_flow": {
        "sequence": ["booking_id", "modification_type", "new_details", "confirmation"],
        "required": ["booking_id", "modification_type"],
        "auth_required": True
    }
}

# ============================================
# SENTIMENT ANALYSIS KEYWORDS
# ============================================

SENTIMENT_KEYWORDS = {
    "positive": [
        "great", "excellent", "amazing", "wonderful", "fantastic", "perfect",
        "love", "happy", "satisfied", "pleased", "delighted", "impressed",
        "thank", "thanks", "appreciate", "helpful", "good", "nice", "awesome"
    ],
    
    "negative": [
        "bad", "poor", "terrible", "horrible", "awful", "disappointed",
        "unhappy", "unsatisfied", "angry", "frustrated", "annoyed", "upset",
        "complaint", "issue", "problem", "not good", "not satisfied", "worst"
    ],
    
    "urgent": [
        "urgent", "emergency", "immediately", "asap", "right now", "critical",
        "help", "stuck", "serious", "quickly", "fast", "hurry"
    ],
    
    "confused": [
        "confused", "don't understand", "unclear", "what", "huh", "explain",
        "clarify", "not clear", "complicated", "difficult"
    ]
}

# ============================================
# RESPONSE PERSONALIZATION
# ============================================

PERSONALIZATION_RULES = {
    "new_user": {
        "greeting_style": "welcoming",
        "explanation_depth": "detailed",
        "offer_guidance": True,
        "suggest_popular": True
    },
    
    "returning_user": {
        "greeting_style": "familiar",
        "explanation_depth": "concise",
        "reference_history": True,
        "personalized_offers": True
    },
    
    "vip_user": {
        "greeting_style": "premium",
        "priority_support": True,
        "exclusive_offers": True,
        "direct_manager_access": True
    },
    
    "business_hours": {
        "response_time": "immediate",
        "human_transfer": "available",
        "phone_support": "active"
    },
    
    "after_hours": {
        "response_time": "automated",
        "human_transfer": "next_business_day",
        "emergency_only": True
    }
}

# ============================================
# CONVERSATION FLOW HELPERS
# ============================================

def get_time_based_greeting():
    """Return time-appropriate greeting"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Hello"

def extract_entities(message):
    """Extract entities from user message"""
    entities = {}
    
    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group()
                break
    
    return entities

def calculate_intent_confidence(message, intent_data):
    """Calculate confidence score for intent matching"""
    score = 0
    message_lower = message.lower()
    
    # Primary keywords
    for keyword in intent_data.get("primary_keywords", []):
        if keyword in message_lower:
            score += 3
    
    # Secondary keywords
    for keyword in intent_data.get("secondary_keywords", []):
        if keyword in message_lower:
            score += 1
    
    # Pattern matching
    for pattern in intent_data.get("patterns", []):
        if re.search(pattern, message_lower):
            score += 5
    
    # Negative keywords (reduce confidence)
    for keyword in intent_data.get("negative_keywords", []):
        if keyword in message_lower:
            score -= 2
    
    # Confidence boost from metadata
    score += intent_data.get("confidence_boost", 0) * 10
    
    # Normalize to 0-1 range
    return min(score / 10, 1.0)

def detect_sentiment(message):
    """Detect sentiment of user message"""
    message_lower = message.lower()
    
    positive_count = sum(1 for word in SENTIMENT_KEYWORDS["positive"] if word in message_lower)
    negative_count = sum(1 for word in SENTIMENT_KEYWORDS["negative"] if word in message_lower)
    urgent_count = sum(1 for word in SENTIMENT_KEYWORDS["urgent"] if word in message_lower)
    
    if urgent_count > 0:
        return "urgent"
    elif negative_count > positive_count:
        return "negative"
    elif positive_count > negative_count:
        return "positive"
    else:
        return "neutral"

def should_escalate(message, sentiment):
    """Determine if query should be escalated to human"""
    message_lower = message.lower()
    
    # Escalation triggers
    escalation_triggers = [
        "speak to manager", "talk to human", "not helpful",
        "this is ridiculous", "terrible service", "refund",
        "legal action", "sue", "complaint", "emergency"
    ]
    
    # Check triggers
    for trigger in escalation_triggers:
        if trigger in message_lower:
            return True
    
    # Negative sentiment with high intensity
    if sentiment == "negative" or sentiment == "urgent":
        return True
    
    return False

# ============================================
# EXPORT ALL
# ============================================

__all__ = [
    'EXPANDED_KNOWLEDGE_BASE',
    'INTENT_PATTERNS',
    'ENTITY_PATTERNS',
    'CONTEXT_RULES',
    'SENTIMENT_KEYWORDS',
    'PERSONALIZATION_RULES',
    'get_time_based_greeting',
    'extract_entities',
    'calculate_intent_confidence',
    'detect_sentiment',
    'should_escalate'
]
INTENT_PATTERNS = {
    "group_event_inquiry": {
        "messages": [
            "events@nur-e-haya.com\n\n**We offer:**\n✨ Special group rates (10–25% discount)\n✨ Customized packages for weddings, conferences, corporate stays\n✨ Dedicated event coordinator\n✨ Flexible payment terms\n✨ Complimentary meeting rooms/banquet facilities\n\n**Popular for:** Corporate retreats, Destination weddings, Family reunions, Business conferences\n\nShould I help you calculate an approximate quote or connect you with our events team?",
            "Planning something special? We'd love to host your group! 🌟\n\n**Group Booking Benefits:**\n• Rooms from ₹2,000/night (bulk discounts available)\n• Block multiple rooms at once\n• Customized meal packages\n• Event coordination support\n• Flexible check-in/out for groups\n\n**Contact our Events Team:**\n📧 events@nur-e-haya.com\n📞 +91 8010572845 (Ext: 2)\n⏰ Response within 2 hours\n\n**Perfect for:** Weddings, Conferences, Corporate offsites, Sports teams, Tour groups\n\nTell me more about your event and I can guide you better!"
        ],
        "related_intents": ["pricing_inquiry", "event_inquiry"],
        "escalation_trigger": True,
        "escalation_department": "events"
    },

    "cancellation_policy": {
        "intent": "cancellation_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["cancel", "cancellation", "refund", "money back", "policy"],
        "entities": ["booking_id", "cancellation_reason"],
        "patterns": [
            r"cancel(lation)? policy",
            r"(how to|can i) cancel",
            r"(get|receive) (a )?refund",
            r"refund policy",
            r"cancel (my )?(booking|reservation)",
            r"cancellation (charges|fee)",
            r"money back"
        ],
        "context_required": False,
        "responses": [
            "Here's our transparent cancellation policy:\n\n**💰 Refund Schedule:**\n\n✅ **48+ hours before check-in**\n   → Full refund (100%)\n   → No questions asked!\n\n⚠️ **24-48 hours before check-in**\n   → 50% refund\n   → Partial cancellation fee applies\n\n❌ **Less than 24 hours before check-in**\n   → No refund\n   → Full amount forfeited\n\n**📋 How to Cancel:**\n1. Log into your dashboard\n2. Go to 'MY BOOKINGS'\n3. Select your booking\n4. Click 'Cancel Booking' button\n5. Confirm cancellation\n6. Refund processed in 5-7 business days\n\n**⚡ Need immediate cancellation?** Call +91 8010572845\n\n**Note:** Refunds go back to original payment method. Special circumstances? Contact support@nur-e-haya.com\n\nDo you need to cancel a booking right now?",
            
            "Let me break down our cancellation policy simply:\n\n**🕐 Timing is Everything:**\n\n🟢 **Cancel MORE than 48 hours early**\n• Get 100% money back\n• Zero penalty\n• Refund in 5-7 days\n\n🟡 **Cancel 24-48 hours before**\n• Get 50% money back\n• 50% cancellation charge\n• Partial refund in 5-7 days\n\n🔴 **Cancel LESS than 24 hours before**\n• Sorry, no refund possible\n• Full amount non-refundable\n• Room already blocked for you\n\n**🔧 To Cancel:**\nDashboard → MY BOOKINGS → Select Booking → Cancel Button → Confirm\n\n**OR**\n\n📞 Call: +91 8010572845 (24/7 support)\n📧 Email: support@nur-e-haya.com\n\n**💡 Pro Tip:** Check your check-in date before canceling to know your refund amount!\n\nWould you like help calculating your potential refund?"
        ],
        "follow_up_questions": [
            "Would you like to cancel an existing booking?",
            "Do you want to know the refund amount for your specific booking?",
            "Can I help you reschedule instead of canceling?"
        ],
        "related_intents": ["booking_modification", "refund_processing"],
        "critical_information": True
    },

    # ============================================
    # ROOM INFORMATION
    # ============================================
    "room_types": {
        "intent": "pricing_inquiry",
        "confidence_boost": 0.1,
        "keywords": ["room", "rooms", "types", "categories", "accommodation", "suite", "luxury"],
        "entities": ["room_type", "guest_count"],
        "patterns": [
            r"(what|which) (room )?types",
            r"(room|accommodation) (options|choices|available)",
            r"(different|all) rooms",
            r"(single|double|suite|luxury|family) room",
            r"room categories"
        ],
        "context_required": False,
        "responses": [
            "We offer 5 luxury accommodation options:\n\n**🛏️ SINGLE ROOM - ₹2,500/night**\n• Perfect for: Solo travelers\n• Capacity: 1 guest\n• Features: King bed, work desk, WiFi, AC, Smart TV\n• Best for: Business travelers, solo adventurers\n\n**🛏️ DOUBLE ROOM - ₹4,000/night**\n• Perfect for: Couples\n• Capacity: 2 guests\n• Features: Queen bed, seating area, WiFi, AC, Smart TV, Room service\n• Best for: Romantic getaways, honeymoons\n\n**🏨 SUITE - ₹5,000/night**\n• Perfect for: Small families\n• Capacity: 3 guests\n• Features: Bedroom + living area, Mini bar, Premium bath, WiFi, AC, Smart TV\n• Best for: Families with child, comfortable stays\n\n**👨‍👩‍👧‍👦 FAMILY ROOM - ₹2,000/night**\n• Perfect for: Budget families (BEST VALUE!)\n• Capacity: 4 guests\n• Features: 2 double beds, spacious, WiFi, AC, Smart TV, Room service\n• Best for: Family vacations, group friends\n\n**🌟 LUXURY ROOM - ₹8,000/night**\n• Perfect for: Premium experience\n• Capacity: 4 guests\n• Features: Jacuzzi, Ocean view, Butler service, Mini bar, Premium amenities\n• Best for: Special occasions, luxury seekers\n\n**All rooms include:**\n✓ High-speed WiFi\n✓ Air Conditioning\n✓ Smart TV with Netflix\n✓ 24/7 Room Service\n✓ Premium toiletries\n✓ Daily housekeeping\n\nWhich room interests you? I can check availability!"
        ],
        "follow_up_questions": [
            "How many guests will be staying?",
            "What's your budget per night?",
            "Do you need any special amenities?",
            "When would you like to book?"
        ],
        "related_intents": ["pricing_inquiry", "amenities_inquiry", "booking_inquiry"]
    },

    "room_amenities": {
        "intent": "amenities_inquiry",
        "confidence_boost": 0.1,
        "keywords": ["amenity", "amenities", "facilities", "feature", "features", "included", "comes with"],
        "entities": ["amenity_type", "room_type"],
        "patterns": [
            r"what (amenities|facilities|features)",
            r"(room|hotel) (amenities|facilities)",
            r"what('s| is) included",
            r"(comes|included) with",
            r"(do you have|is there) (a )?(wifi|gym|pool|spa|breakfast)",
            r"in.?room (amenities|facilities)"
        ],
        "context_required": False,
        "responses": [
            "Here's everything we offer! ✨\n\n**🏨 IN EVERY ROOM (Standard Amenities):**\n✅ High-speed WiFi (Fiber 100 Mbps)\n✅ Air Conditioning (Climate control)\n✅ Smart TV (Netflix, Prime Video)\n✅ Premium bedding (Egyptian cotton)\n✅ Private bathroom (Hot/cold water 24/7)\n✅ Complimentary toiletries (Eco-friendly)\n✅ In-room safe\n✅ Tea/coffee maker\n✅ Hair dryer\n✅ Iron & ironing board\n✅ 24/7 Room Service\n✅ Daily housekeeping\n\n**🌟 UPGRADED ROOMS ONLY (Suite, Luxury):**\n🍹 Mini Bar (stocked daily)\n🛁 Jacuzzi/Premium bathtub\n🌅 Ocean/City views\n👔 Butler Service (Luxury only)\n🍾 Welcome drinks\n🎁 Premium bath products\n\n**🏢 HOTEL FACILITIES:**\n🍽️ Multi-cuisine restaurant\n☕ 24/7 café\n💼 Business center\n🎪 Banquet halls\n🚗 Free parking\n🚕 Airport shuttle (on request)\n🧳 Luggage storage\n🛎️ Concierge service\n🏪 Gift shop\n\n**🌐 SERVICES:**\n✓ Laundry & dry cleaning\n✓ Doctor on call\n✓ Travel desk\n✓ Currency exchange\n✓ Taxi booking\n✓ Tour arrangements\n\nNeed specific info about any amenity?"
        ],
        "follow_up_questions": [
            "Are you looking for specific amenities?",
            "Which room type are you interested in?",
            "Do you need accessibility features?"
        ],
        "related_intents": ["room_types", "special_requests"]
    },

    # ============================================
    # CHECK-IN/CHECK-OUT
    # ============================================
    "checkin_checkout_times": {
        "intent": "checkin_checkout",
        "confidence_boost": 0.15,
        "keywords": ["check in", "check out", "check-in", "check-out", "time", "timing", "arrival", "departure"],
        "entities": ["time", "early_late_request"],
        "patterns": [
            r"check.?in (time|timing|hours)",
            r"check.?out (time|timing|hours)",
            r"(what time|when) (can|do|should) (i|we) check.?in",
            r"(what time|when) (is|do|should) check.?out",
            r"(arrival|departure) (time|timing)",
            r"(early|late) (check.?in|check.?out)"
        ],
        "context_required": False,
        "responses": [
            "Here are our check-in/check-out timings:\n\n**🏨 STANDARD TIMINGS:**\n\n✅ **CHECK-IN:**\n• Time: 2:00 PM onwards\n• What you need: Valid photo ID + booking confirmation\n• Process: Quick 5-minute registration\n• Early arrival? Luggage storage available!\n\n✅ **CHECK-OUT:**\n• Time: 11:00 AM\n• Process: Quick 2-minute checkout\n• Late departure? Luggage storage available!\n\n**⏰ FLEXIBLE TIMINGS:**\n\n🌅 **Early Check-in (Before 2 PM):**\n• Subject to availability\n• May incur extra charges\n• Request while booking or call ahead\n• Best chance: Weekdays, off-season\n\n🌙 **Late Check-out (After 11 AM):**\n• Up to 6 PM: 50% of room rate\n• After 6 PM: Full night charge\n• Request at least 24 hours in advance\n• Subject to availability\n\n**💡 PRO TIPS:**\n• Request early/late during booking\n• Call +91 8010572845 24 hours ahead\n• Weekday requests more likely approved\n• Loyalty members get priority!\n\n**📞 Need special timing?**\nCall: +91 8010572845\nEmail: support@nur-e-haya.com\n\nWould you like to request early check-in or late check-out?"
        ],
        "follow_up_questions": [
            "Do you need early check-in?",
            "Would you like late check-out?",
            "What time do you expect to arrive?",
            "When is your flight/train?"
        ],
        "related_intents": ["special_requests", "booking_inquiry"],
        "critical_information": True
    },

    # ============================================
    # PAYMENT & PRICING
    # ============================================
    "payment_methods": {
        "intent": "payment_methods",
        "confidence_boost": 0.12,
        "keywords": ["payment", "pay", "card", "upi", "netbanking", "wallet", "method", "options"],
        "entities": ["payment_type"],
        "patterns": [
            r"payment (method|option|mode|way)",
            r"how (to|can|do|do i) pay",
            r"(accept|take|support) (card|upi|netbanking|wallet)",
            r"payment (accepted|available)",
            r"(credit|debit) card",
            r"(which|what) payment"
        ],
        "context_required": False,
        "responses": [
            "We accept ALL major payment methods for your convenience! 💳\n\n**💳 CREDIT & DEBIT CARDS:**\n✓ Visa, Mastercard, American Express, RuPay\n✓ Domestic & International cards\n✓ 100% secure 3D authentication\n✓ Instant confirmation\n\n**🏦 NET BANKING:**\n✓ All major Indian banks (SBI, HDFC, ICICI, Axis, etc.)\n✓ 100+ banks supported\n✓ Direct bank transfer\n✓ No extra charges\n\n**📱 UPI (MOST POPULAR!):**\n✓ Google Pay, PhonePe, Paytm, BHIM\n✓ Scan QR code or enter UPI ID\n✓ Instant payment\n✓ Zero transaction fee\n\n**👛 DIGITAL WALLETS:**\n✓ Paytm, PhonePe, Amazon Pay, Mobikwik\n✓ One-click payment\n✓ Cashback offers available\n\n**🔒 SECURITY FEATURES:**\n✓ 256-bit SSL encryption\n✓ PCI-DSS compliant\n✓ No card details stored\n✓ Secure payment gateway\n✓ Instant transaction confirmation\n\n**💰 PAYMENT POLICIES:**\n• Full payment at booking time\n• No hidden charges\n• Refunds to original payment method\n• Process time: 5-7 business days\n\n**🎁 PROMO CODES:**\n• WELCOME10 - 10% off first booking\n• SAVE500 - ₹500 flat discount\n• LUXURY20 - 20% off luxury rooms\n\n**Need help with payment?**\n📞 +91 8010572845 (24/7 support)\n\nWhich payment method would you prefer?"
        ],
        "follow_up_questions": [
            "Would you like to know about payment security?",
            "Do you have a promo code?",
            "Need help completing payment?"
        ],
        "related_intents": ["booking_inquiry", "promo_codes"]
    },

    # ============================================
    # LOCATION & TRANSPORT
    # ============================================
    "location_directions": {
        "intent": "location_transport",
        "confidence_boost": 0.12,
        "keywords": ["location", "address", "where", "directions", "how to reach", "find"],
        "entities": ["transport_mode", "starting_point"],
        "patterns": [
            r"(where|what) (is|are) (you|your|the|hotel) (location|address)",
            r"how to (reach|get to|find)",
            r"(hotel )?(location|address|directions)",
            r"where (is|are) you",
            r"how (do i|can i) (reach|get there)"
        ],
        "context_required": False,
        "responses": [
            "We're centrally located for easy access! 📍\n\n**🏨 HOTEL ADDRESS:**\nNur-e-Haya Luxury Hotel\n[Complete Address]\n[City, State - PIN]\n\n**📱 GOOGLE MAPS:**\n[Link: maps.google.com/nur-e-haya]\n→ Click for live navigation!\n\n**✈️ FROM AIRPORT:**\n• Distance: 15 km\n• By Taxi: 25-30 mins (₹400-500)\n• By Metro: 40 mins (₹60)\n• **Free Shuttle:** Book 24hrs ahead!\n\n**🚂 FROM RAILWAY STATION:**\n• Distance: 8 km\n• By Taxi: 15-20 mins (₹200-300)\n• By Metro: 25 mins (₹40)\n• **Free Shuttle:** Available!\n\n**🚇 NEAREST METRO:**\n• Station: [Name] (2 km)\n• Walking: 20 mins\n• Auto: 5 mins (₹50)\n\n**🚕 LOCAL TRANSPORT:**\n• Taxis readily available\n• Uber/Ola: Always accessible\n• Auto-rickshaws nearby\n• Hotel taxi service available\n\n**🅿️ PARKING:**\n• Free parking for guests\n• 50+ vehicle capacity\n• CCTV surveillance\n• Valet service available\n\n**🗺️ NEARBY LANDMARKS:**\n• City Mall: 1 km\n• Beach: 3 km\n• Business District: 4 km\n• Tourist Spots: 2-10 km\n\n**📞 LOST? CALL US:**\n+91 8010572845\nWe'll guide you step-by-step!\n\nNeed directions from a specific location?"
        ],
        "follow_up_questions": [
            "Where are you traveling from?",
            "Do you need airport shuttle service?",
            "Would you like taxi booking assistance?",
            "Need directions from a specific location?"
        ],
        "related_intents": ["airport_shuttle", "parking_info"]
    },
    "booking_inquiry": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["book", "reserve", "reservation", "availability", "available"],
        "secondary_keywords": ["room", "stay", "check in", "want to", "need"],
        "negative_keywords": ["cancel", "modify", "change"],
        "variations": [
            "i want to book", "how do i book", "book a room", "make a reservation",
            "reserve a room", "are rooms available", "check availability",
            "can i book", "booking process", "want to reserve"
        ]
    },
    "booking_modification": {
        "confidence_threshold": 0.75,
        "primary_keywords": ["modify", "change", "update", "edit", "reschedule"],
        "secondary_keywords": ["booking", "reservation", "date", "room"],
        "variations": [
            "change my booking", "modify reservation", "update my booking",
            "reschedule my stay", "change dates", "extend my stay"
        ]
    },
    "cancellation_inquiry": {
        "confidence_threshold": 0.8,
        "primary_keywords": ["cancel", "cancellation", "refund"],
        "secondary_keywords": ["booking", "reservation", "policy", "money back"],
        "variations": [
            "cancel my booking", "cancellation policy", "how to cancel",
            "get a refund", "cancel reservation"
        ]
    },
    "pricing_inquiry": {
        "confidence_threshold": 0.7,
        "primary_keywords": ["price", "cost", "rate", "charge", "expensive", "cheap"],
        "secondary_keywords": ["room", "stay", "night", "how much"],
        "variations": [
            "how much does it cost", "room prices", "what are the rates",
            "price per night", "cheapest room"
        ]
    },


    "airport_shuttle": {
        "intent": "location_transport",
        "confidence_boost": 0.15,
        "keywords": ["airport", "shuttle", "pickup", "drop", "transfer", "transport"],
        "entities": ["flight_time", "terminal"],
        "patterns": [
            r"airport (shuttle|pickup|drop|transfer|service)",
            r"(pick|pickup|drop|transport) (from|to) airport",
            r"airport transport(ation)?",
            r"complimentary (shuttle|pickup|transfer)"
        ],
        "context_required": False,
        "responses": [
            "Yes! We offer FREE airport shuttle service! ✈️🚐\n\n**🆓 COMPLIMENTARY SHUTTLE:**\n\n**✅ PICKUP (Airport → Hotel):**\n• Completely FREE for all guests!\n• Available 24/7\n• AC vehicles\n• Professional drivers\n• Meet & greet at arrivals\n• Luggage assistance\n\n**✅ DROP (Hotel → Airport):**\n• Completely FREE for all guests!\n• Available 24/7\n• Timely departures\n• Flight tracking\n• Zero stress!\n\n**📋 HOW TO BOOK:**\n\n**During Booking:**\n→ Fill 'Special Requests' with:\n  • Flight number\n  • Arrival/departure time\n  • Terminal number\n  • Number of passengers\n\n**After Booking:**\n→ Email: support@nur-e-haya.com\n→ Call: +91 8010572845\n→ WhatsApp: +91-XXXXX-XXXXX\n\n**⏰ BOOKING REQUIREMENTS:**\n• Book at least 24 hours in advance\n• Provide accurate flight details\n• Notify if flight delayed/early\n\n**🚐 VEHICLE DETAILS:**\n• Clean, AC vehicles\n• Comfortable seating (4-6 passengers)\n• Ample luggage space\n• GPS tracked\n• COVID sanitized\n\n**⏱️ TRAVEL TIME:**\n• Airport to Hotel: 25-30 mins\n• Hotel to Airport: 25-35 mins\n• (Depending on traffic)\n\n**📱 ON ARRIVAL:**\n• Driver will wait at Arrivals\n• Holding placard with your name\n• Will help with luggage\n• Direct to hotel\n\n**💡 PRO TIPS:**\n• Share flight updates if delayed\n• We track flights automatically\n• For groups: Mention passenger count\n• Early morning/late night? No problem!\n\n**CONTACT FOR BOOKING:**\n📞 +91 8010572845\n📧 support@nur-e-haya.com\n💬 WhatsApp: +91-XXXXX-XXXXX\n\nReady to book your free shuttle?"
        ],
        "follow_up_questions": [
            "What's your flight number?",
            "What time do you land/depart?",
            "Which terminal?",
            "How many passengers?"
        ],
        "related_intents": ["location_directions", "special_requests"],
        "booking_required": True
    },
    "accessibility_general": {
    "intent": "accessibility_inquiry",
    "confidence_boost": 0.15,
    "keywords": ["disabled", "disability", "wheelchair", "accessible", "accessibility", "handicap", "special needs", "mobility"],
    "entities": ["accessibility_type"],
    "patterns": [
        r"(wheelchair|disabled|handicap) (accessible|friendly|access)",
        r"(do you have|is there) (wheelchair )?accessibility",
        r"facilities for disabled",
        r"special needs (guest|accommodation)",
        r"mobility (issues|impaired|assistance)"
    ],
    "context_required": False,
    "responses": [
        "**♿ ACCESSIBILITY FOR DISABLED GUESTS**\n\nYes! We provide accessibility facilities:\n\n**Available Features:**\n✓ Wheelchair-accessible rooms\n✓ Ramps at all entrances\n✓ Elevator access to all floors\n✓ Wide doorways (32 inches)\n✓ Accessible parking spaces\n✓ Ground floor rooms available\n\n**To Know More:**\n• Ask about wheelchair access\n• Ask about bathroom accessibility\n• Ask about visual/hearing assistance\n• Ask about staff support\n\n📞 Special Requirements? Call +91 8010572845\n\nWhat specific accessibility feature would you like to know about?",
        
        "**♿ ACCESSIBILITY SUPPORT**\n\nWe welcome guests with disabilities!\n\n**Our Facilities Include:**\n• Wheelchair-friendly rooms\n• Barrier-free pathways\n• Accessible bathrooms\n• Elevator to all floors\n• Assistance available 24/7\n• Ground floor accommodation\n\n**You Can Ask About:**\n→ Wheelchair accessibility\n→ Bathroom grab bars & features\n→ Visual/hearing assistance\n→ Mobility support services\n→ Emergency evacuation procedures\n\nWhat would you like to know specifically?"
    ],
    "follow_up_questions": [
        "What type of accessibility do you need?",
        "Wheelchair access?",
        "Bathroom accessibility?",
        "Need staff assistance information?"
    ],
    "related_intents": ["wheelchair_access", "bathroom_accessibility"]
    },

    "wheelchair_access": {
        "intent": "accessibility_inquiry",
        "confidence_boost": 0.18,
        "keywords": ["wheelchair", "ramp", "wide door", "pathway", "corridor", "elevator", "lift"],
        "entities": [],
        "patterns": [
            r"wheelchair (access|accessible|entry|ramp)",
            r"(wide|wider) (door|doorway|entrance)",
            r"(elevator|lift) access",
            r"ramp (available|entrance)",
            r"wheelchair (friendly|compatible)"
        ],
        "context_required": False,
        "responses": [
            "**♿ WHEELCHAIR ACCESSIBILITY**\n\n**Building Access:**\n✓ Ramps at main entrance (1:12 slope)\n✓ Ramps at all entry points\n✓ No steps to reception\n✓ Automatic sliding doors\n✓ Zero threshold entry\n\n**Room Access:**\n✓ Wide doorways (32 inches minimum)\n✓ Corridor width: 48 inches\n✓ Lever-style door handles (easy grip)\n✓ Low peepholes (wheelchair height)\n✓ Ground floor rooms available\n\n**Elevator:**\n✓ Wheelchair-accessible lift\n✓ Wide cabin (4ft × 5ft)\n✓ Braille buttons\n✓ Audio announcements\n✓ Emergency assistance button\n\n**Parking:**\n✓ 2 designated accessible parking spots\n✓ Near main entrance\n✓ Extra wide spaces\n✓ Covered parking available\n\n**Pathways:**\n✓ Smooth, level flooring\n✓ No uneven surfaces\n✓ Non-slip tiles\n✓ Well-lit corridors\n\nAll wheelchair users can move independently!",
            
            "**♿ WHEELCHAIR-FRIENDLY FEATURES**\n\n✓ **Entrance:** Ramps with handrails, no stairs\n✓ **Doors:** 32\"+ wide, automatic/lever handles\n✓ **Elevator:** Spacious, Braille & audio-enabled\n✓ **Rooms:** Ground floor option, wide entry\n✓ **Corridors:** 48\" wide, obstacle-free\n✓ **Parking:** Designated accessible spots\n✓ **Reception:** Lowered counter for wheelchair users\n✓ **Restaurant:** Wheelchair-accessible seating\n\n**Maneuverability:**\n• 5-foot turning radius in rooms\n• Smooth transitions (no bumps)\n• Clear pathways throughout\n\n**Need wheelchair assistance?** Our staff can help with:\n• Luggage handling\n• Room navigation\n• Transportation coordination\n\n📞 Advance notice appreciated: +91 8010572845"
        ],
        "related_intents": ["accessibility_general", "bathroom_accessibility"]
    },

    "bathroom_accessibility": {
        "intent": "accessibility_inquiry",
        "confidence_boost": 0.18,
        "keywords": ["grab bar", "handrail", "accessible bathroom", "disabled toilet", "roll-in shower", "wheelchair bathroom"],
        "entities": [],
        "patterns": [
            r"(accessible|disabled|wheelchair) (bathroom|toilet|shower)",
            r"grab bar",
            r"(hand)?rail (in )?bathroom",
            r"roll.?in shower",
            r"toilet (grab bar|safety bar|handrail)"
        ],
        "context_required": False,
        "responses": [
            "**♿ ACCESSIBLE BATHROOM FEATURES**\n\n**Toilet Area:**\n✓ Raised toilet seat (17-19 inches height)\n✓ Grab bars on both sides\n✓ Wall-mounted horizontal bars\n✓ L-shaped grab bar for transfer\n✓ Adequate space (5ft turning radius)\n✓ Emergency pull cord\n\n**Shower/Bath:**\n✓ Roll-in shower (no threshold)\n✓ Hand-held shower head (adjustable)\n✓ Wall-mounted grab bars\n✓ Shower bench/transfer seat\n✓ Non-slip flooring\n✓ Lever-style faucets (easy turn)\n\n**Sink/Vanity:**\n✓ Wall-hung sink (knee clearance below)\n✓ Lowered mirror (wheelchair height)\n✓ Single-lever faucet\n✓ Accessible storage shelves\n✓ Grab bar near sink\n\n**Safety Features:**\n✓ Emergency call button\n✓ Pull cord near toilet/shower\n✓ Slip-resistant flooring\n✓ Adequate lighting\n✓ Door opens outward (more space)\n\n**Door:**\n✓ 32 inches wide\n✓ Lever handle\n✓ Easy-open mechanism\n\nAll safety standards met!",
            
            "**🚿 DISABILITY-FRIENDLY BATHROOMS**\n\n**Key Features:**\n\n🚽 **Toilet:**\n• Comfort-height (ADA compliant)\n• Grab bars: both sides + behind\n• Space for wheelchair transfer\n• Emergency alert system\n\n🚿 **Shower:**\n• Zero-entry roll-in design\n• Fold-down shower seat\n• Hand-held shower wand\n• Horizontal & vertical grab bars\n• Anti-slip mat\n\n🪞 **Sink Area:**\n• Wheelchair accessible (open below)\n• Lowered counter height\n• Easy-grip lever taps\n• Tilted mirror\n\n⚠️ **Safety:**\n• Emergency call button\n• Pull cord at multiple points\n• Responds to front desk immediately\n• 24/7 assistance available\n\n**Dimensions:**\n• Doorway: 32 inches\n• Turning space: 5 feet diameter\n• Toilet clearance: 30×48 inches\n\n📞 Need specific modifications? Call ahead: +91 8010572845"
        ],
        "related_intents": ["accessibility_general", "wheelchair_access"]
    },

    "visual_hearing_assistance": {
        "intent": "accessibility_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["blind", "deaf", "hearing", "visual", "braille", "sign language", "impaired", "visually impaired", "hearing impaired"],
        "entities": [],
        "patterns": [
            r"(blind|visually impaired|vision)",
            r"(deaf|hearing impaired|hard of hearing)",
            r"braille",
            r"sign language",
            r"(visual|hearing) (assistance|impairment|disability)"
        ],
        "context_required": False,
        "responses": [
            "**👁️👂 VISUAL & HEARING ASSISTANCE**\n\n**For Visually Impaired Guests:**\n✓ Braille room numbers on doors\n✓ Braille elevator buttons\n✓ Tactile floor indicators\n✓ Audio announcements in elevators\n✓ Guide dog friendly (service animals welcome)\n✓ Staff trained to assist\n✓ Braille menu cards (restaurant)\n✓ Voice-guided room orientation\n\n**For Hearing Impaired Guests:**\n✓ Visual fire alarms (flashing lights)\n✓ Doorbell with light indicator\n✓ Vibrating alarm clock available\n✓ TV with closed captioning\n✓ Text-based communication options\n✓ Written instructions in room\n✓ Staff basic sign language trained\n✓ Video call interpretation available\n\n**Communication:**\n✓ WhatsApp text support: +91-XXXXX-XXXXX\n✓ Email communication preferred\n✓ Written check-in/check-out process\n✓ Visual room orientation\n\n**Emergency:**\n✓ Visual & audio alert systems\n✓ Text-based emergency contact\n✓ Staff trained for assistance\n\n**Service Animals:**\n✓ Guide dogs welcome (no charge)\n✓ Assistance animals accommodated\n✓ Bowls & bedding provided\n\n📧 Email us in advance: support@nur-e-haya.com\n\nWe ensure independent & comfortable stays!",
            
            "**👁️ VISUAL IMPAIRMENT SUPPORT:**\n• Braille signage throughout\n• Tactile pathways to rooms\n• Audio guidance in elevators\n• Guide dogs fully welcome\n• Textured floor indicators\n• Staff assistance on call\n• Large-print materials available\n• Voice room number announcements\n\n**👂 HEARING IMPAIRMENT SUPPORT:**\n• Flashing light fire alarms\n• Doorbell with visual flash\n• Vibrating pillow alarm clocks\n• Closed-caption TV\n• Written communication options\n• Text message check-in\n• Visual emergency alerts\n• Basic sign language staff\n\n**📱 Communication Methods:**\n• WhatsApp: Text-based support\n• Email: support@nur-e-haya.com\n• Video call with interpreter\n• Written notes welcomed\n\n**🐕 Service Animals:**\nGuide/assistance dogs fully permitted with:\n• Food/water bowls\n• Comfortable bedding\n• Designated relief areas\n\n**📞 Pre-Arrival Coordination:**\nContact us 24-48 hours ahead:\n+91 8010572845 (voice/text)\nsupport@nur-e-haya.com\n\nWe'll prepare your room accordingly!"
        ],
        "related_intents": ["accessibility_general", "special_requests"]
    },

    "mobility_assistance_service": {
        "intent": "accessibility_inquiry",
        "confidence_boost": 0.15,
        "keywords": ["staff help", "assistance", "support", "attendant", "caregiver", "mobility help", "escort"],
        "entities": [],
        "patterns": [
            r"staff (help|assistance|support)",
            r"(need|require) assistance",
            r"help (with|for) (mobility|movement|walking)",
            r"(attendant|caregiver|escort) available",
            r"someone to help"
        ],
        "context_required": False,
        "responses": [
            "**🤝 STAFF ASSISTANCE SERVICES**\n\n**Available Support:**\n\n✓ **Check-in/Check-out Assistance:**\n• Luggage handling\n• Paperwork help\n• Room escort service\n• Vehicle-to-room assistance\n\n✓ **Mobility Support:**\n• Wheelchair provision (free)\n• Walker/crutches available\n• Staff escort to room/restaurant\n• Help with door opening\n• Emergency assistance 24/7\n\n✓ **Daily Assistance:**\n• Room service delivery\n• Extra housekeeping visits\n• Medicine reminder service\n• Meal assistance (if needed)\n• Communication relay\n\n✓ **Emergency Response:**\n• 24/7 front desk monitoring\n• Medical emergency protocol\n• Hospital coordination\n• Doctor on call\n\n**How to Request:**\n📞 Call reception: Dial 0 from room\n🔔 Press room service button\n📧 Email: support@nur-e-haya.com\n💬 Inform at check-in\n\n**Caregiver/Companion:**\n✓ Extra person in room allowed (discuss at booking)\n✓ Additional bed/rollaway available\n✓ No extra charge for caregiver stay\n\n**Advance Notice Recommended:**\nContact 24 hours ahead for:\n• Wheelchair arrangements\n• Special room setups\n• Multiple assistance needs\n• Medical equipment storage\n\n📞 +91 8010572845\n\nOur staff is trained and always ready to help!",
            
            "**🫱🏽‍🫲🏽 ASSISTANCE & SUPPORT SERVICES**\n\n**Immediate Help Available:**\n• Wheelchair (complimentary)\n• Staff escort/guidance\n• Luggage carry assistance\n• Door-to-door support\n• 24/7 emergency response\n\n**Trained Staff:**\nOur team is trained in:\n• Wheelchair assistance\n• Transfer support\n• Basic first aid\n• Emergency evacuation procedures\n• Sensitivity & respect\n\n**Request Assistance:**\n1. Call front desk (dial 0)\n2. Press emergency button in room\n3. Inform at check-in\n4. Pre-book via phone/email\n\n**Companion/Caregiver:**\n• Can stay in same room\n• Additional bed provided\n• No extra charge (discuss at booking)\n• Access to all facilities\n\n**Medical Support:**\n• Doctor on call (24/7)\n• First aid kit in reception\n• Hospital 5km away\n• Pharmacy nearby\n• Ambulance coordination\n\n**Special Equipment:**\nWe can arrange:\n• Wheelchair (free)\n• Walker/cane\n• Hospital bed (advance notice)\n• Commode chair\n• Oxygen cylinder (with prescription)\n\n📞 Advance booking recommended:\n+91 8010572845\nsupport@nur-e-haya.com\n\nYour comfort and safety come first!"
        ],
        "related_intents": ["accessibility_general", "special_requests"]
    },
}


ENTITY_PATTERNS = {
    "date": [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"(today|tomorrow|next week|next month)"
    ],
    "guest_count": [
        r"(\d+) (guest|guests|people|persons)"
    ],
    "room_type": [
        r"(single|double|suite|luxury|family) room"
    ],
    "email": [
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    ],
    "price_range": [
        r"(under|below|less than|up to) ₹?\d+"
    ]
}

# ============================================
# CONTEXT RULES
# ============================================

CONTEXT_RULES = {
    "booking_flow": {
        "sequence": ["dates", "guests", "room_type", "special_requests", "payment"],
        "required": ["dates", "guests", "room_type"]
    },
    "complaint_flow": {
        "sequence": ["issue_description", "severity", "urgency"],
        "required": ["issue_description"]
    }
}

# ============================================
# SENTIMENT ANALYSIS
# ============================================

SENTIMENT_KEYWORDS = {
    "positive": ["great", "excellent", "love", "helpful", "good", "awesome"],
    "negative": ["bad", "poor", "terrible", "complaint", "issue"],
    "urgent": ["urgent", "immediately", "asap", "help", "emergency"]
}

# ============================================
# PERSONALIZATION
# ============================================

PERSONALIZATION_RULES = {
    "new_user": {"greeting_style": "welcoming"},
    "returning_user": {"greeting_style": "familiar"},
    "vip_user": {"greeting_style": "premium"}
}

# ============================================
# UTILITIES
# ============================================

def get_time_based_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 22:
        return "Good evening"
    else:
        return "Hello"

def extract_entities(message):
    entities = {}
    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                entities[entity_type] = match.group()
                break
    return entities

def calculate_intent_confidence(message, intent_data):
    score = 0
    msg = message.lower()
    for k in intent_data.get("primary_keywords", []):
        if k in msg: score += 3
    for k in intent_data.get("secondary_keywords", []):
        if k in msg: score += 1
    for pat in intent_data.get("variations", []):
        if pat in msg: score += 4
    for k in intent_data.get("negative_keywords", []):
        if k in msg: score -= 2
    score += intent_data.get("confidence_boost", 0) * 10
    return min(score / 10, 1.0)

def detect_sentiment(message):
    msg = message.lower()
    pos = sum(1 for w in SENTIMENT_KEYWORDS["positive"] if w in msg)
    neg = sum(1 for w in SENTIMENT_KEYWORDS["negative"] if w in msg)
    urg = sum(1 for w in SENTIMENT_KEYWORDS["urgent"] if w in msg)
    if urg > 0:
        return "urgent"
    elif neg > pos:
        return "negative"
    elif pos > neg:
        return "positive"
    return "neutral"

def should_escalate(message, sentiment):
    msg = message.lower()
    triggers = ["speak to manager", "talk to human", "not helpful", "refund", "emergency"]
    if any(t in msg for t in triggers):
        return True
    return sentiment in ["negative", "urgent"]

# ============================================
# EXPORTS
# ============================================

__all__ = [
    "INTENT_PATTERNS",
    "ENTITY_PATTERNS",
    "CONTEXT_RULES",
    "SENTIMENT_KEYWORDS",
    "PERSONALIZATION_RULES",
    "get_time_based_greeting",
    "extract_entities",
    "calculate_intent_confidence",
    "detect_sentiment",
    "should_escalate"
]