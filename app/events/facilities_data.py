"""
facilities_data.py - Master Catalog of Spa & Hotel Facilities
Structured into 5 Distinct Luxury Subsections:
1. The Royal Ayur Spa & Wellness Sanctuaries
2. Skyline Heated Infinity Pool & Private Cabanas
3. TechnoGym Fitness Arena & Thermal Suites
4. Yoga, Prāṇāyāma & Sound Meditation Pavilion
5. The Royal Salon & Executive Grooming
"""

FACILITY_SECTIONS = [
    {
        "id": "spa",
        "title": "The Royal Ayur Spa & Wellness Sanctuaries",
        "category": "Ayurvedic Spa & Wellness",
        "subtitle": "Ancient Ayurvedic healing wisdom fused with Turkish hammam therapies and restorative bodywork.",
        "icon": "fas fa-spa",
        "badge": "Holistic Healing"
    },
    {
        "id": "pool",
        "title": "Skyline Heated Infinity Pool & Private Cabanas",
        "category": "Pool & Cabanas",
        "subtitle": "Panoramic 14th-floor heated infinity pool, hydrotherapy jets, sunset lounge seating, and VIP cabanas.",
        "icon": "fas fa-water",
        "badge": "Rooftop Views"
    },
    {
        "id": "fitness",
        "title": "TechnoGym Fitness Arena & Thermal Suites",
        "category": "Fitness & Thermal",
        "subtitle": "24/7 high-performance cardio, Olympic weights, Finnish dry cedar sauna, and certified coaching.",
        "icon": "fas fa-dumbbell",
        "badge": "24/7 Access"
    },
    {
        "id": "yoga",
        "title": "Yoga, Prāṇāyāma & Sound Meditation Pavilion",
        "category": "Yoga & Meditation",
        "subtitle": "Open-air rooftop glass sanctuary for sunrise hatha flows, Tibetan singing bowls, and chakra alignment.",
        "icon": "fas fa-om",
        "badge": "Mindfulness"
    },
    {
        "id": "salon",
        "title": "The Royal Salon & Executive Grooming",
        "category": "Salon & Grooming",
        "subtitle": "Bespoke gentleman's barbering, Ayurvedic hair rituals, luxury manicures, and red-carpet bridal styling.",
        "icon": "fas fa-cut",
        "badge": "Couture Styling"
    }
]

FACILITIES_DATA = [
    # -------------------------------------------------------------------------
    # 1. AYURVEDIC SPA & WELLNESS
    # -------------------------------------------------------------------------
    {
        "id": "fac_spa_abhyanga",
        "name": "Abhyanga Full-Body Warm Herbal Oil Massage",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 3500,
        "duration": "75 mins",
        "image": "https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=800&q=80",
        "description": "Traditional synchronized warm medicated sesame oil massage following ancient Vedic marma lines to detoxify the lymphatic system, release muscle tightness, and restore vital prana energy.",
        "benefits": [
            "Deep lymphatic drainage and metabolic detoxification",
            "Enhances microcirculation and natural skin radiance",
            "Relieves nervous exhaustion, anxiety, and insomnia",
            "Includes complimentary herbal steam bath post-treatment"
        ],
        "location": "Floor 3, East Wellness Wing",
        "inclusions": "Custom warm herbal oils, private herbal steam room, organic ginger infusion tea, luxury locker & plush robe.",
        "rating": 4.9,
        "reviews_count": 142,
        "slots": ["08:00 AM", "10:30 AM", "01:00 PM", "03:30 PM", "06:00 PM", "08:30 PM"]
    },
    {
        "id": "fac_spa_shirodhara",
        "name": "Shirodhara Mind Calming & Stress Relief Therapy",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 4200,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1600334129128-685c5582fd35?auto=format&fit=crop&w=800&q=80",
        "description": "A continuous rhythmic stream of warm herbalized medicated oil poured gently across the forehead and third-eye chakra, harmonizing brainwaves and dissolving persistent mental stress.",
        "benefits": [
            "Clinically proven reduction in stress and mental fatigue",
            "Stimulates deep restorative REM sleep cycles",
            "Alleviates chronic tension headaches and migraines",
            "Nourishes hair roots with medicated brahmi and amla oils"
        ],
        "location": "Floor 3, Ayurvedic Sanctuary",
        "inclusions": "Brahmi-infused warm oil stream, warm towel head wrap, cranial acupressure, soothing saffron tea.",
        "rating": 4.95,
        "reviews_count": 98,
        "slots": ["09:00 AM", "11:30 AM", "02:00 PM", "04:30 PM", "07:00 PM"]
    },
    {
        "id": "fac_spa_kizhi",
        "name": "Kizhi Herbal Poultice & Joint Relieving Therapy",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 3800,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1519823551278-64ac92734fb1?auto=format&fit=crop&w=800&q=80",
        "description": "Warm muslin pouches packed with therapeutic medicinal leaves, roots, and spices dipped in hot medicated oils and rhythmically tapped along aching joints, knees, and the spine.",
        "benefits": [
            "Rapid relief for acute lower backache and joint stiffness",
            "Reduces inflammatory muscular swellings",
            "Restores spinal mobility and athletic flexibility",
            "Soothes deep chronic muscle fatigue"
        ],
        "location": "Floor 3, East Wellness Wing",
        "inclusions": "Handcrafted organic leaf poultices, specialized mahanarayan pain-relief oils, heated compress.",
        "rating": 4.88,
        "reviews_count": 76,
        "slots": ["08:30 AM", "11:00 AM", "01:30 PM", "04:00 PM", "06:30 PM"]
    },
    {
        "id": "fac_spa_hammam",
        "name": "Royal Turkish Hammam & Eucalyptus Foam Bath",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 4800,
        "duration": "90 mins",
        "image": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?auto=format&fit=crop&w=800&q=80",
        "description": "An authentic Ottoman bathing ritual performed on heated marble. Includes black olive soap cleansing, coarse kessa glove exfoliation, cloud-soft eucalyptus foam wash, and argan hydration.",
        "benefits": [
            "Total epidermal detoxification and dead skin exfoliation",
            "Leaves skin velvety smooth and deeply moisturized",
            "Eucalyptus herbal steam clarifies airways and sinuses",
            "Deep muscular release on warm anatomical marble slab"
        ],
        "location": "Floor 3, Ottoman Hammam Suite",
        "inclusions": "Traditional Turkish peshtemal silk towel, copper bowl water pours, organic Moroccan argan massage.",
        "rating": 4.97,
        "reviews_count": 115,
        "slots": ["10:00 AM", "01:00 PM", "04:00 PM", "07:00 PM"]
    },
    {
        "id": "fac_spa_balinese",
        "name": "Balinese Deep Tissue & Volcanic Hot Stone Fusion",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 4500,
        "duration": "90 mins",
        "image": "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=800&q=80",
        "description": "A rigorous synergy of firm thumb kneading, long skin rolling, and heated volcanic basalt stones aligned along energy meridians to dissolve deep fibrous tension.",
        "benefits": [
            "Releases chronic structural postural knots",
            "Penetrates deep into tight myofascial tissue",
            "Accelerates athletic recovery and lactic acid clearance",
            "Induces a profound state of tranquil rejuvenation"
        ],
        "location": "Floor 3, East Wellness Wing",
        "inclusions": "Volcanic basalt stones, lemongrass-ginger aromatic oil blend, thermal herbal compress.",
        "rating": 4.92,
        "reviews_count": 89,
        "slots": ["09:30 AM", "12:00 PM", "02:30 PM", "05:00 PM", "07:30 PM"]
    },
    {
        "id": "fac_spa_facial",
        "name": "Royal 24K Gold Radiance Botanical Facial",
        "category": "Ayurvedic Spa & Wellness",
        "section_id": "spa",
        "price": 3200,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=800&q=80",
        "description": "A radiant complexion facial featuring pure 24-karat bio-gold leaf application, wild saffron brightening nectar, gentle micro-exfoliation, and chilled rose quartz lymphatic sculpting.",
        "benefits": [
            "Instant luminous glow and deeply revitalized texture",
            "Stimulates collagen and elastin regeneration",
            "Eliminates facial puffiness with chilled rose quartz",
            "Fades hyperpigmentation and sun-induced dullness"
        ],
        "location": "Floor 3, Beauty Sanctuary",
        "inclusions": "24K gold leaves, cold-pressed botanical essences, rose quartz lymphatic roll, gold collagen mask.",
        "rating": 4.91,
        "reviews_count": 104,
        "slots": ["10:00 AM", "12:30 PM", "03:00 PM", "05:30 PM", "08:00 PM"]
    },

    # -------------------------------------------------------------------------
    # 2. SKYLINE HEATED INFINITY POOL & PRIVATE CABANAS
    # -------------------------------------------------------------------------
    {
        "id": "fac_pool_hydro",
        "name": "Heated Infinity Pool Hydrotherapy & Lap Swim",
        "category": "Pool & Cabanas",
        "section_id": "pool",
        "price": 1200,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?auto=format&fit=crop&w=800&q=80",
        "description": "Swim atop the city skyline in our 14th-floor heated infinity pool kept at a soothing 29°C year-round. Features cervical waterfall jets, underwater audio, and panoramic vistas.",
        "benefits": [
            "Decompresses spinal joints via warm water buoyancy",
            "Invigorating full-body cardiovascular workout",
            "Unrivaled 14th-floor panoramic skyline view",
            "Complimentary access for all Suite & Luxury room guests"
        ],
        "location": "Floor 14, Rooftop Sky Deck",
        "inclusions": "Heated infinity pool access, oversized Egyptian cotton towels, sun lounger, underwater sound system.",
        "rating": 4.96,
        "reviews_count": 210,
        "slots": ["06:00 AM", "07:30 AM", "09:00 AM", "11:00 AM", "02:00 PM", "04:30 PM", "07:00 PM"]
    },
    {
        "id": "fac_pool_cabana_vip",
        "name": "VIP Private Heated Cabana & Refreshments Lounge",
        "category": "Pool & Cabanas",
        "section_id": "pool",
        "price": 3500,
        "duration": "120 mins",
        "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80",
        "description": "An exclusive private curtained cabana with plush daybeds on the rooftop pool deck. Comes with personal butler service, chilled eucalyptus towels, and fresh tropical refreshments.",
        "benefits": [
            "Complete secluded poolside privacy for up to 4 guests",
            "Dedicated on-demand butler bell service",
            "Curated exotic seasonal fruit platter & craft mocktails",
            "High-speed poolside Wi-Fi and device charging hub"
        ],
        "location": "Floor 14, Poolside Terrace",
        "inclusions": "2 signature craft mocktails, seasonal fruit skewers, cold water bottles, cooling botanical face mist.",
        "rating": 4.98,
        "reviews_count": 87,
        "slots": ["10:00 AM", "12:30 PM", "03:00 PM", "05:30 PM", "08:00 PM"]
    },
    {
        "id": "fac_pool_sunset",
        "name": "Sunset Skyline Swim & Craft Mocktail Experience",
        "category": "Pool & Cabanas",
        "section_id": "pool",
        "price": 1800,
        "duration": "90 mins",
        "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?auto=format&fit=crop&w=800&q=80",
        "description": "Bathe in golden-hour brilliance with soothing twilight ambient music, underwater fiber-optic illumination, warm 29°C waters, and poolside chef's tapas.",
        "benefits": [
            "Best golden-hour photography vantage point in the city",
            "Curated chillout acoustics & twilight mood lighting",
            "Heated comfort as the evening air cools down",
            "Includes handcrafted mocktail and gourmet poolside canapés"
        ],
        "location": "Floor 14, Sunset Sky Lounge",
        "inclusions": "Signature sunset mocktail, Chef's tapas taster plate, reserved sunset lounger.",
        "rating": 4.94,
        "reviews_count": 134,
        "slots": ["05:00 PM", "06:45 PM"]
    },
    {
        "id": "fac_pool_aqua",
        "name": "Aqua Aerobics & Water Resistance Class",
        "category": "Pool & Cabanas",
        "section_id": "pool",
        "price": 1500,
        "duration": "45 mins",
        "image": "https://images.unsplash.com/photo-1530549387789-4c1017266635?auto=format&fit=crop&w=800&q=80",
        "description": "Low-impact, high-calorie burn aquatic conditioning led by certified hydro-fitness coaches. Uses buoyant foam dumbbells and water resistance noodles.",
        "benefits": [
            "Burns up to 450 kcal with zero joint impact",
            "High resistance toning for core, arms, and legs",
            "Safe for rehabilitation, prenatal, or sensitive knees",
            "Fun, energizing small-group atmosphere"
        ],
        "location": "Floor 14, Rooftop Sky Pool",
        "inclusions": "Hydro-dumbbells, resistance belts, post-workout electrolyte smoothie.",
        "rating": 4.87,
        "reviews_count": 62,
        "slots": ["08:00 AM", "10:00 AM", "04:00 PM"]
    },

    # -------------------------------------------------------------------------
    # 3. TECHNOGYM FITNESS ARENA & THERMAL SUITES
    # -------------------------------------------------------------------------
    {
        "id": "fac_gym_pass",
        "name": "TechnoGym Elite Cardio & Strength Full-Day Access",
        "category": "Fitness & Thermal",
        "section_id": "fitness",
        "price": 800,
        "duration": "Full Day Pass",
        "image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=800&q=80",
        "description": "All-day pass to our 24/7 fitness arena featuring TechnoGym Artis consoles with virtual world courses, Olympic free weights, dumbbell racks up to 50kg, and cable machines.",
        "benefits": [
            "TechnoGym Artis cardio displays with Netflix & virtual routes",
            "Olympic barbells, bumper plates, and dual cable stations",
            "24/7 keycard access anytime day or night",
            "Full access to luxury showers and grooming amenities"
        ],
        "location": "Floor 4, South Fitness Wing",
        "inclusions": "Infused lemon-cucumber water, sweat towels, digital locker access, luxury shower suites.",
        "rating": 4.93,
        "reviews_count": 188,
        "slots": ["Full Day Access (24/7)"]
    },
    {
        "id": "fac_gym_trainer",
        "name": "1-on-1 Certified Master Personal Training Session",
        "category": "Fitness & Thermal",
        "section_id": "fitness",
        "price": 2000,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?auto=format&fit=crop&w=800&q=80",
        "description": "Tailored training guided by an ACE/ISSA certified master coach. Includes biometric body-composition analysis, movement screening, and customized progressive overload.",
        "benefits": [
            "InBody 770 clinical body composition scan",
            "Biomechanical assessment to eliminate posture imbalances",
            "Custom-targeted HIIT, hypertrophy, or fat-loss workout",
            "Post-workout assisted stretching and recovery blueprint"
        ],
        "location": "Floor 4, Personal Training Studio",
        "inclusions": "InBody diagnostic report, custom exercise roadmap, post-workout protein recovery shake.",
        "rating": 4.95,
        "reviews_count": 79,
        "slots": ["06:30 AM", "08:30 AM", "11:00 AM", "03:00 PM", "05:30 PM", "07:30 PM"]
    },
    {
        "id": "fac_gym_sauna",
        "name": "Finnish Dry Cedarwood Sauna & Cold Plunge Circuit",
        "category": "Fitness & Thermal",
        "section_id": "fitness",
        "price": 1400,
        "duration": "45 mins",
        "image": "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=800&q=80",
        "description": "Contrast thermal recovery protocol. Cycle between our 85°C dry Scandinavian cedar sauna, 12°C ice-cold plunge tub, and eucalyptus mist rainfall shower for a surge in vitality.",
        "benefits": [
            "Spikes norepinephrine and mental alertness",
            "Accelerates post-exercise muscle recovery and DOMS relief",
            "Boosts cardiovascular circulation and vascular elasticity",
            "Triggers heat-shock and cold-shock restorative proteins"
        ],
        "location": "Floor 4, Thermal Recovery Suite",
        "inclusions": "Cedarwood sauna access, chilled plunge bath, eucalyptus aroma spray, waffle robe & slide slippers.",
        "rating": 4.96,
        "reviews_count": 112,
        "slots": ["07:00 AM", "09:00 AM", "01:00 PM", "04:00 PM", "06:30 PM", "08:30 PM"]
    },
    {
        "id": "fac_gym_hiit",
        "name": "HIIT & Olympic Functional Strength Coaching",
        "category": "Fitness & Thermal",
        "section_id": "fitness",
        "price": 1600,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=800&q=80",
        "description": "High-octane functional conditioning incorporating sled turf pushes, heavy battle ropes, plyo jump boxes, kettlebell complexes, and Concept2 rowers.",
        "benefits": [
            "Elevates EPOC metabolic afterburn for up to 36 hours",
            "Increases VO2 max and anaerobic stamina",
            "Builds lean functional athletic muscle",
            "Energizing playlist and small-group coaching feedback"
        ],
        "location": "Floor 4, Functional Turf Arena",
        "inclusions": "Heart-rate monitor loan, intra-workout BCAA drink, chilled eucalyptus towel.",
        "rating": 4.89,
        "reviews_count": 55,
        "slots": ["07:00 AM", "09:30 AM", "05:00 PM", "07:00 PM"]
    },

    # -------------------------------------------------------------------------
    # 4. YOGA, PRĀṆĀYĀMA & SOUND MEDITATION PAVILION
    # -------------------------------------------------------------------------
    {
        "id": "fac_yoga_sunrise",
        "name": "Sunrise Hatha Yoga & Guided Prāṇāyāma",
        "category": "Yoga & Meditation",
        "section_id": "yoga",
        "price": 1200,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=800&q=80",
        "description": "Salute the rising dawn from our open-air glass rooftop pavilion. Classical Surya Namaskar series followed by gentle spinal extension and balanced Nadi Shodhana breathing.",
        "benefits": [
            "Expands respiratory vital capacity and breath control",
            "Gently releases morning joint stiffness and opens hips",
            "Instills tranquil mental focus for the day ahead",
            "Suitable for beginners and experienced yogis alike"
        ],
        "location": "Floor 14, Rooftop Zen Glass Pavilion",
        "inclusions": "Manduka Pro eco-mat, organic cork blocks, warm Himalayan tulsi herbal tea.",
        "rating": 4.97,
        "reviews_count": 165,
        "slots": ["06:30 AM", "07:45 AM"]
    },
    {
        "id": "fac_yoga_soundbath",
        "name": "Tibetan Singing Bowl Sound Bath & Chakra Alignment",
        "category": "Yoga & Meditation",
        "section_id": "yoga",
        "price": 2200,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1512290900672-1f0289f81df6?auto=format&fit=crop&w=800&q=80",
        "description": "Surrender to acoustic sonic resonance as 7 handcrafted bronze Himalayan singing bowls, wind gongs, and Koshi chimes guide your brain into restorative theta wave states.",
        "benefits": [
            "Dissolves deep emotional and cognitive stress",
            "Slows overactive brainwaves into meditative theta states",
            "Harmonizes the seven subtle energy chakras",
            "Alleviates deep-seated travel fatigue and restlessness"
        ],
        "location": "Floor 14, Sound Healing Sanctuary",
        "inclusions": "Lavender silk eye pillow, cashmere throw blanket, organic grounding chamomile tea.",
        "rating": 4.99,
        "reviews_count": 121,
        "slots": ["05:30 PM", "07:00 PM"]
    },
    {
        "id": "fac_yoga_sunset_med",
        "name": "Sunset Mindful Breathwork & Guided Zen Meditation",
        "category": "Yoga & Meditation",
        "section_id": "yoga",
        "price": 1000,
        "duration": "45 mins",
        "image": "https://images.unsplash.com/photo-1545205597-3d9d02c29597?auto=format&fit=crop&w=800&q=80",
        "description": "Transition gently from daytime stimulation into evening peace. Features guided physiological box breathing, progressive somatic body relaxation, and mindful silence.",
        "benefits": [
            "Downregulates sympathetic nervous system and cortisol",
            "Prepares mind and body for deep natural slumber",
            "Cultivates profound inner presence and equanimity",
            "Ideal antidote for jet lag and cognitive fatigue"
        ],
        "location": "Floor 14, Rooftop Zen Glass Pavilion",
        "inclusions": "Buckwheat zafu cushion, Mysore sandalwood incense, warm nightcap herbal blend.",
        "rating": 4.88,
        "reviews_count": 73,
        "slots": ["06:15 PM", "07:15 PM"]
    },
    {
        "id": "fac_yoga_private",
        "name": "Private Restorative Yin Yoga Masterclass",
        "category": "Yoga & Meditation",
        "section_id": "yoga",
        "price": 2500,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=800&q=80",
        "description": "One-on-one session holding supportive floor postures for 3-5 minutes with bolsters and blankets to gently release deep connective tissue, tendons, and fascia.",
        "benefits": [
            "Deep fascial unwinding in the hips, pelvis, and lumbar spine",
            "Calms nervous system through sustained gentle compression",
            "Personalized alignment adjustments tailored to your anatomy",
            "Uninterrupted, private studio atmosphere"
        ],
        "location": "Floor 14, Private Yoga Studio",
        "inclusions": "Certified master yogi instructor, organic cotton bolsters, essential oil aromatherapy.",
        "rating": 4.95,
        "reviews_count": 48,
        "slots": ["09:00 AM", "11:30 AM", "02:30 PM", "04:30 PM"]
    },

    # -------------------------------------------------------------------------
    # 5. THE ROYAL SALON & EXECUTIVE GROOMING
    # -------------------------------------------------------------------------
    {
        "id": "fac_salon_shave",
        "name": "Gentleman's Royal Hot Towel Shave & Scalp Massage",
        "category": "Salon & Grooming",
        "section_id": "salon",
        "price": 1500,
        "duration": "45 mins",
        "image": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?auto=format&fit=crop&w=800&q=80",
        "description": "The quintessential gentleman's grooming ritual. Steamed lavender hot towels, rich badger-hair lather, precision single-edge razor shave, and soothing sandalwood balm scalp rub.",
        "benefits": [
            "Impeccably clean, ultra-close comfortable shave",
            "Prevents razor burn and ingrown hairs with pre-shave oils",
            "Relieves cranial tension through acupressure scalp massage",
            "Relaxation in an antique Belmont barber chair"
        ],
        "location": "Floor 3, The Royal Barber Lounge",
        "inclusions": "Sandalwood aftershave balm, chilled alum stone rub, artisanal espresso or scotch.",
        "rating": 4.94,
        "reviews_count": 139,
        "slots": ["09:00 AM", "10:30 AM", "12:00 PM", "02:30 PM", "04:00 PM", "06:00 PM"]
    },
    {
        "id": "fac_salon_hairspa",
        "name": "Ayurvedic Kesh Kanti Hair Spa & Steam Ritual",
        "category": "Salon & Grooming",
        "section_id": "salon",
        "price": 2400,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1560750588-73207b1ef5b8?auto=format&fit=crop&w=800&q=80",
        "description": "Deep restorative hair rejuvenation with warm cold-pressed Bhringraj and Amla oils, stimulating scalp acupressure, micro-mist ionic steam, and a nourishing botanical mask.",
        "benefits": [
            "Deeply fortifies hair follicles from root to tip",
            "Eliminates scalp dryness, dandruff, and seasonal itchiness",
            "Restores glossy shine and silky bounce to heat-damaged hair",
            "Includes stress-relieving upper neck and shoulder massage"
        ],
        "location": "Floor 3, Royal Salon",
        "inclusions": "Warm herbal scalp oils, ionic micro-mist ozone steam, professional blowout finish.",
        "rating": 4.91,
        "reviews_count": 92,
        "slots": ["10:00 AM", "11:30 AM", "02:00 PM", "04:00 PM", "06:30 PM"]
    },
    {
        "id": "fac_salon_manipedi",
        "name": "Luxury Himalayan Salt Manicure & Pedicure Ritual",
        "category": "Salon & Grooming",
        "section_id": "salon",
        "price": 2000,
        "duration": "60 mins",
        "image": "https://images.unsplash.com/photo-1632345031435-8727f6897d53?auto=format&fit=crop&w=800&q=80",
        "description": "Warm botanical foot soak with pink Himalayan mineral crystals, sugar-cane exfoliation, nail and cuticle refinement, heated paraffin booties, and lower-leg massage.",
        "benefits": [
            "Restores baby-soft texture to dry heels and calluses",
            "Relieves aching feet and swollen ankles after travel",
            "Professional nail shaping and high-gloss buff or organic tint",
            "Deep hydration with warm shea butter paraffin wrap"
        ],
        "location": "Floor 3, Nail Spa Lounge",
        "inclusions": "Himalayan crystal foot soak, warm paraffin wrap, cuticle conditioning, organic nail lacquer.",
        "rating": 4.89,
        "reviews_count": 108,
        "slots": ["10:00 AM", "12:00 PM", "02:00 PM", "04:00 PM", "06:00 PM"]
    },
    {
        "id": "fac_salon_bridal",
        "name": "Royal Bridal & Gala Styling Consultation",
        "category": "Salon & Grooming",
        "section_id": "salon",
        "price": 5500,
        "duration": "120 mins",
        "image": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=800&q=80",
        "description": "Master-level red carpet and wedding event styling. Includes customized high-definition makeup, intricate hair updo styling, sari/gown draping, and setting mist for 12+ hour perfection.",
        "benefits": [
            "1-on-1 consultation with senior celebrity artist",
            "Camera-ready sweat-resistant HD makeup and contouring",
            "Artisanal fresh floral insertion and hair couture",
            "Private luxury bridal preparation dressing suite"
        ],
        "location": "Floor 3, VIP Couture Suite",
        "inclusions": "Master artist, touch-up kit, veil/dupatta pin-up, glass of complimentary champagne.",
        "rating": 4.99,
        "reviews_count": 64,
        "slots": ["10:00 AM", "02:00 PM", "05:00 PM"]
    }
]
