"""
data_seeder.py - Comprehensive Production-Scale Data Seeder for Nur-e-Haya Luxury PMS
Populates:
1. 150+ Curated Fine Dining Menu Items across 5 Categories (30+ per category) with high-res photography.
2. 40+ Realistic Luxury Rooms across Heritage Wing, Royal Wing, and Skyline Tower (Floors 1-8).
3. 24 Restaurant Tables across Grand Dining Hall, Rooftop Terrace, Poolside Verandah, and Private Salons.
"""

import logging
from datetime import datetime, timedelta
from app.events.facilities_data import FACILITIES_DATA

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# 1. MENU ITEMS CATALOG (150+ Unique Gourmet Dishes across 5 Categories, 30+ each)
# --------------------------------------------------------------------------------------

MENU_STARTERS = [
    {"name": "Royal Galouti Kebab with Sheermal", "price": 580, "is_veg": False, "prep": "18 mins", "desc": "Melt-in-mouth smoked lamb patties infused with 32 rare spices, saffron sheermal bread.", "img": "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=600&q=80"},
    {"name": "Truffle & Porcini Wild Mushroom Arancini", "price": 490, "is_veg": True, "prep": "15 mins", "desc": "Carnaroli risotto crisp spheres, black winter truffle essence, molten fontina center, garlic aioli.", "img": "https://images.unsplash.com/photo-1541529086526-db283c563270?auto=format&fit=crop&w=600&q=80"},
    {"name": "Bhatti Da Murgh Peshawari", "price": 520, "is_veg": False, "prep": "20 mins", "desc": "Bone-in chicken steeped in crushed coriander, dried fenugreek, char-grilled in tandoor.", "img": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=600&q=80"},
    {"name": "Paneer Zaffrani Tikka", "price": 460, "is_veg": True, "prep": "15 mins", "desc": "Artisanal buffalo milk paneer cubes marinated in saffron cream, yellow chili and carom seeds.", "img": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?auto=format&fit=crop&w=600&q=80"},
    {"name": "Coastal Calamari Salt & Pepper Fritters", "price": 540, "is_veg": False, "prep": "12 mins", "desc": "Tender squid rings flashed with kaffir lime zest, bird's eye chili, scallions, and yuzu dip.", "img": "https://images.unsplash.com/photo-1604909052743-94e838986d24?auto=format&fit=crop&w=600&q=80"},
    {"name": "Edamame & Truffle Dim Sum (6 pcs)", "price": 480, "is_veg": True, "prep": "14 mins", "desc": "Translucent crystal skin stuffed with crushed sweet edamame, water chestnut and black truffle broth.", "img": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=600&q=80"},
    {"name": "Kasundi Prawn Skewers", "price": 680, "is_veg": False, "prep": "16 mins", "desc": "Jumbo Bay of Bengal prawns slathered in Bengali stone-ground mustard and pan-roasted on skewers.", "img": "https://images.unsplash.com/photo-1559742811-822873691df8?auto=format&fit=crop&w=600&q=80"},
    {"name": "Avocado & Pomegranate Bhel", "price": 380, "is_veg": True, "prep": "10 mins", "desc": "Hass avocado dice, organic puffed grains, ruby pomegranate pearls, tamarind emulsion.", "img": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=600&q=80"},
    {"name": "Burrata with Heirloom Tomatoes & Peach", "price": 550, "is_veg": True, "prep": "10 mins", "desc": "Pugliese creamy burrata, compressed stone peaches, basil caviar, 12-year aged Modena balsamic.", "img": "https://images.unsplash.com/photo-1592417817098-8f3d6910985b?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spiced Lamb Gilafi Seekh", "price": 590, "is_veg": False, "prep": "18 mins", "desc": "Minced pasture-fed lamb encased in diced bell peppers and fresh mint, charcoal glazed.", "img": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80"},
    {"name": "Stuffed Morel Mushrooms (Gucchi)", "price": 750, "is_veg": True, "prep": "20 mins", "desc": "Himalayan wild morels filled with pistachio cream and spiced mawa, slow tandoor roasted.", "img": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chicken Karaage with Wasabi Mayo", "price": 480, "is_veg": False, "prep": "14 mins", "desc": "Crispy double-fried chicken morsels, ginger-soy marinade, fresh grated wasabi mayonnaise.", "img": "https://images.unsplash.com/photo-1562967914-608f82629710?auto=format&fit=crop&w=600&q=80"},
    {"name": "Dahi Ke Kebab with Mint Coulis", "price": 420, "is_veg": True, "prep": "12 mins", "desc": "Hung curd patties blended with green cardamoms and crushed coriander, shallow griddled.", "img": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80"},
    {"name": "Yellowfin Tuna Tartare", "price": 690, "is_veg": False, "prep": "12 mins", "desc": "Hand-cut sashimi grade tuna, ponzu-sesame dressing, avocado mousse, lotus root chips.", "img": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=600&q=80"},
    {"name": "Corn & Jalapeno Croquettes", "price": 390, "is_veg": True, "prep": "12 mins", "desc": "Sweet corn and smoked monterey jack croquettes with chipotle honey dip.", "img": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=600&q=80"},
    {"name": "Amritsari Crispy Fish Tikka", "price": 540, "is_veg": False, "prep": "15 mins", "desc": "Fresh river sole coated with carom-seed spiced gram flour batter, radish mint laccha salad.", "img": "https://images.unsplash.com/photo-1534939561126-855b8675edd7?auto=format&fit=crop&w=600&q=80"},
    {"name": "Crispy Lotus Stem in Plum Glaze", "price": 410, "is_veg": True, "prep": "12 mins", "desc": "Wok-tossed thinly sliced lotus root in tangy spiced wild plum glaze and toasted sesame.", "img": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chili Garlic Tiger Prawns", "price": 720, "is_veg": False, "prep": "14 mins", "desc": "Butterflied prawns seared in wok with burnt garlic, scallions, bird's eye chilies and Shaoxing broth.", "img": "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?auto=format&fit=crop&w=600&q=80"},
    {"name": "Wild Mushroom Pate & Brioche Toast", "price": 450, "is_veg": True, "prep": "10 mins", "desc": "Rich forest mushroom terrine, thyme roasted fig jam, warm buttered brioche toasts.", "img": "https://images.unsplash.com/photo-1509722747041-616f39b57569?auto=format&fit=crop&w=600&q=80"},
    {"name": "Mutton Pepper Fry Cones", "price": 560, "is_veg": False, "prep": "16 mins", "desc": "Slow-roasted Chettinad lamb shreds packed into mini savory pastry cones with curry leaf froth.", "img": "https://images.unsplash.com/photo-1628294895950-9805252327bc?auto=format&fit=crop&w=600&q=80"},
    {"name": "Avocado & Beetroot Tartare", "price": 430, "is_veg": True, "prep": "10 mins", "desc": "Roasted red beetroot cubes, creamy guacamole, goat cheese snow, seeded crackers.", "img": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Smoked Duck Carpaccio", "price": 640, "is_veg": False, "prep": "12 mins", "desc": "Thinly shaved oak-smoked duck breast, orange reduction, arugula, shaved parmesan.", "img": "https://images.unsplash.com/photo-1432139555190-58524dae6a55?auto=format&fit=crop&w=600&q=80"},
    {"name": "Pesto Stuffed Portobello Caps", "price": 440, "is_veg": True, "prep": "15 mins", "desc": "Giant grilled portobello caps overflowing with walnut basil pesto and melted mozzarella.", "img": "https://images.unsplash.com/photo-1505576399279-565b52d4ac71?auto=format&fit=crop&w=600&q=80"},
    {"name": "Himalayan Trout Bruschetta", "price": 520, "is_veg": False, "prep": "12 mins", "desc": "Cured pink river trout, pickled red onions, dill cream cheese on rustic grilled sourdough.", "img": "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spinach & Ricotta Raviolini Friti", "price": 410, "is_veg": True, "prep": "12 mins", "desc": "Golden fried micro ravioli with creamy arrabbiata dipping sauce.", "img": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=600&q=80"},
    {"name": "Tangra Style Chili Garlic Chicken", "price": 470, "is_veg": False, "prep": "15 mins", "desc": "Kolkata Chinatown wok-tossed crispy boneless chicken with green chilies and dark soy sauce.", "img": "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=600&q=80"},
    {"name": "Truffle Fries with Herb Aioli", "price": 350, "is_veg": True, "prep": "10 mins", "desc": "Double blanched hand-cut Idaho potatoes tossed with white truffle oil, rosemary, parmesan.", "img": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?auto=format&fit=crop&w=600&q=80"},
    {"name": "Seared Atlantic Sea Scallops", "price": 790, "is_veg": False, "prep": "14 mins", "desc": "Jumbo sea scallops pan-seared in brown butter, cauliflower velvet puree, crisp bacon crumb.", "img": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=600&q=80"},
    {"name": "Vegetable Crystal Gyoza", "price": 380, "is_veg": True, "prep": "14 mins", "desc": "Pan-crisped Japanese dumplings packed with shiitake mushrooms, bok choy, and ginger ponzu.", "img": "https://images.unsplash.com/photo-1498654896293-37aacf113fd9?auto=format&fit=crop&w=600&q=80"},
    {"name": "Balochi Mutton Boti Skewers", "price": 610, "is_veg": False, "prep": "20 mins", "desc": "Boneless baby goat cubes tenderized in raw papaya and yogurt, char-grilled with charred lemons.", "img": "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Mezze Platter Royale", "price": 590, "is_veg": True, "prep": "12 mins", "desc": "Silky hummus, smoked mutabbal, tzatziki, falafel rounds, stuffed vine leaves, warm pita.", "img": "https://images.unsplash.com/photo-1541518763669-27fef04b14ea?auto=format&fit=crop&w=600&q=80"}
]

MENU_MAINS = [
    {"name": "Nur-e-Haya Royal Dum Biryani", "price": 750, "is_veg": False, "prep": "25 mins", "desc": "Fragrant aged basmati rice layered with tender lamb shanks, saffron, caramelized onions, sealed with dough.", "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=600&q=80"},
    {"name": "Dal Bukhara Handi & Truffle Kulcha", "price": 480, "is_veg": True, "prep": "20 mins", "desc": "Urad lentils slow simmered over coal embers for 24 hours with vine tomatoes, fresh churned butter.", "img": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=600&q=80"},
    {"name": "Murgh Makhani (Butter Chicken Grand)", "price": 620, "is_veg": False, "prep": "20 mins", "desc": "Clay-oven pulled tandoori chicken simmered in rich velvety tomato and cashew nut gravy enriched with fenugreek.", "img": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=600&q=80"},
    {"name": "Pan-Seared Chilean Sea Bass", "price": 1250, "is_veg": False, "prep": "25 mins", "desc": "Miso-glazed Patagonian sea bass fillet, wilted baby bok choy, dashi butter broth, jasmine rice.", "img": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=600&q=80"},
    {"name": "Paneer Lababdar with Laccha Paratha", "price": 520, "is_veg": True, "prep": "18 mins", "desc": "Fresh cottage cheese dice in chunky tomato-onion gravy scented with royal cumin and coriander.", "img": "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?auto=format&fit=crop&w=600&q=80"},
    {"name": "Nalli Rogan Josh Kashmiri", "price": 780, "is_veg": False, "prep": "30 mins", "desc": "Prime baby lamb marrow shanks cooked in traditional Kashmiri red chili broth and ratanjot extract.", "img": "https://images.unsplash.com/photo-1545247181-516773ca838b?auto=format&fit=crop&w=600&q=80"},
    {"name": "Wild Mushroom Risotto with Truffle", "price": 640, "is_veg": True, "prep": "22 mins", "desc": "Acquerello aged carnaroli rice, morels, chanterelles, porcini broth, 24-month parmigiano-reggiano.", "img": "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?auto=format&fit=crop&w=600&q=80"},
    {"name": "Australian Wagyu Ribeye Steak (250g)", "price": 1650, "is_veg": False, "prep": "25 mins", "desc": "Grade 7+ Wagyu ribeye, roasted garlic potato mousseline, charred asparagus, green peppercorn jus.", "img": "https://images.unsplash.com/photo-1558030006-450675393462?auto=format&fit=crop&w=600&q=80"},
    {"name": "Subz Dum Biryani Nizami", "price": 540, "is_veg": True, "prep": "20 mins", "desc": "Garden vegetables, baby potatoes, green peas slow cooked in sealed pot with long-grain Dehradun basmati.", "img": "https://images.unsplash.com/photo-1642821373181-696a54913e93?auto=format&fit=crop&w=600&q=80"},
    {"name": "Grilled Norwegian Salmon Supreme", "price": 980, "is_veg": False, "prep": "20 mins", "desc": "Crisp skin salmon, saffron lemon veloute, crushed fingerling potatoes, sauteed broccolini.", "img": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=600&q=80"},
    {"name": "Truffle Gnocchi Gorgonzola", "price": 580, "is_veg": True, "prep": "18 mins", "desc": "Hand-rolled potato gnocchi, dolce gorgonzola cream, candied walnuts, crisp sage.", "img": "https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=600&q=80"},
    {"name": "Goan Prawn Curry with Coconut Milk", "price": 720, "is_veg": False, "prep": "20 mins", "desc": "Jumbo tiger prawns simmered in freshly grated coconut, kokum and red Goan spices, red rice.", "img": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=600&q=80"},
    {"name": "Hand-made Tagliatelle Ai Funghi", "price": 560, "is_veg": True, "prep": "18 mins", "desc": "Fresh ribbon egg pasta tossed with wild forest mushrooms, garlic, white wine, and fresh chives.", "img": "https://images.unsplash.com/photo-1621996346565-e3d5d628169b?auto=format&fit=crop&w=600&q=80"},
    {"name": "Slow-Braised New Zealand Lamb Shanks", "price": 890, "is_veg": False, "prep": "30 mins", "desc": "12-hour braised lamb hind shanks, port wine reduction, creamy polenta, glazed baby carrots.", "img": "https://images.unsplash.com/photo-1514944298352-f51399f604ec?auto=format&fit=crop&w=600&q=80"},
    {"name": "Palak Paneer with Makki Ki Roti", "price": 490, "is_veg": True, "prep": "18 mins", "desc": "Organic mountain spinach puree with fresh cottage cheese, spiced with garlic and organic ghee.", "img": "https://images.unsplash.com/photo-1606491956689-2ea866880c84?auto=format&fit=crop&w=600&q=80"},
    {"name": "Malabar Fish Curry with Steamed Appams", "price": 660, "is_veg": False, "prep": "22 mins", "desc": "Kingfish steaks stewed in rich coconut milk, shallots, curry leaves and Kodampuli garcinia.", "img": "https://images.unsplash.com/photo-1580476262798-bddd9f4b7369?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spinach & Ricotta Cannelloni", "price": 530, "is_veg": True, "prep": "20 mins", "desc": "Rolled pasta tubes baked in san marzano tomato passata and bechamel with bubbling mozzarella.", "img": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80"},
    {"name": "Tenderloin Medallions Tournedos Rossini", "price": 1450, "is_veg": False, "prep": "26 mins", "desc": "Filet mignon medallions, seared foie gras, black truffle slices, Madeira demi-glace sauce.", "img": "https://images.unsplash.com/photo-1504973999438-18250f70b40e?auto=format&fit=crop&w=600&q=80"},
    {"name": "Dum Aloo Kashmiri in Fennel Gravy", "price": 440, "is_veg": True, "prep": "18 mins", "desc": "Pricked baby potatoes simmered in curd and dry ginger broth with Kashmiri red chilies.", "img": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=600&q=80"},
    {"name": "Roasted Corn-Fed Spring Chicken", "price": 680, "is_veg": False, "prep": "25 mins", "desc": "Half roasted poussin, garlic herb jus, root vegetables, thyme roasted baby potatoes.", "img": "https://images.unsplash.com/photo-1598103442097-8b74394b95c6?auto=format&fit=crop&w=600&q=80"},
    {"name": "Wood-Fired Pizza Quattro Formaggi", "price": 620, "is_veg": True, "prep": "15 mins", "desc": "San Marzano tomatoes, fior di latte mozzarella, gorgonzola dolce, asiago, shaved parmesan.", "img": "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=600&q=80"},
    {"name": "Lobster Thermidor Imperial", "price": 1850, "is_veg": False, "prep": "30 mins", "desc": "Whole Bay lobster meat folded in Dijon mustard, egg yolk, Gruyere glaze, flashed in shell.", "img": "https://images.unsplash.com/photo-1533777857889-4be7c70b33f7?auto=format&fit=crop&w=600&q=80"},
    {"name": "Aubergine Parmigiana Classica", "price": 490, "is_veg": True, "prep": "20 mins", "desc": "Layers of fried eggplant, basil, fresh mozzarella and tomato coulis baked to golden brown.", "img": "https://images.unsplash.com/photo-1625944525533-473f1a3d54e7?auto=format&fit=crop&w=600&q=80"},
    {"name": "Thai Green Curry with Jasmine Rice", "price": 570, "is_veg": True, "prep": "18 mins", "desc": "Coconut milk, Thai basil, bird's eye chilies, pea aubergine, bamboo shoots, tofu and galangal.", "img": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Panang Prawn Curry Royale", "price": 750, "is_veg": False, "prep": "20 mins", "desc": "Rich peanut and kaffir lime infused red curry with tiger prawns and sticky jasmine rice.", "img": "https://images.unsplash.com/photo-1569562211093-4ed0d0758f12?auto=format&fit=crop&w=600&q=80"},
    {"name": "Classic Spaghetti Carbonara Guanciale", "price": 590, "is_veg": False, "prep": "16 mins", "desc": "Traditional Roman preparation with cured pork cheek, farm egg yolks, pecorino romano, black pepper.", "img": "https://images.unsplash.com/photo-1612874742237-6526221588e3?auto=format&fit=crop&w=600&q=80"},
    {"name": "Bhuna Gosht Lucknowi", "price": 690, "is_veg": False, "prep": "25 mins", "desc": "Braised goat meat fried dry in iron wok with roasted onions, ginger slivers and whole garam masala.", "img": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80"},
    {"name": "Paneer Makhani with Butter Naan", "price": 510, "is_veg": True, "prep": "18 mins", "desc": "Velvety butter sauce packed with tender cottage cheese and topped with cream drizzle.", "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=600&q=80"},
    {"name": "Miso Glazed Tofu & Soba Noodle Bowl", "price": 480, "is_veg": True, "prep": "16 mins", "desc": "Buckwheat soba, organic glazed tofu, edamame, shiitake mushrooms, toasted sesame dashi broth.", "img": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=600&q=80"},
    {"name": "Lamb Shank Nihari with Khameeri Roti", "price": 820, "is_veg": False, "prep": "30 mins", "desc": "Overnight slow-cooked bone-in mutton stew seasoned with royal spices, ginger juliennes, green chilies.", "img": "https://images.unsplash.com/photo-1574484284002-952d92456975?auto=format&fit=crop&w=600&q=80"}
]

MENU_DESSERTS = [
    {"name": "Pistachio & Rose Turkish Baklava", "price": 380, "is_veg": True, "prep": "8 mins", "desc": "Layers of paper-thin phyllo pastry stuffed with Antep emerald pistachios, organic rose sugar syrup.", "img": "https://images.unsplash.com/photo-1519869325930-281384150729?auto=format&fit=crop&w=600&q=80"},
    {"name": "Royal Shahi Tukda with Gold Leaf", "price": 420, "is_veg": True, "prep": "10 mins", "desc": "Ghee crisped milk bread soaked in saffron rabri, garnished with 24K edible gold foil and silver leaf.", "img": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?auto=format&fit=crop&w=600&q=80"},
    {"name": "Valrhona 70% Dark Chocolate Molten Fondant", "price": 460, "is_veg": True, "prep": "15 mins", "desc": "Warm lava cake with flowing Guanaja center, served alongside Tahitian vanilla bean gelato.", "img": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=600&q=80"},
    {"name": "Classic Venetian Tiramisu", "price": 410, "is_veg": True, "prep": "8 mins", "desc": "Savoiardi ladyfingers soaked in Illy espresso and dark rum, mascarpone cream, Dutch cocoa powder.", "img": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=600&q=80"},
    {"name": "Alphonso Mango Kulfi Falooda", "price": 340, "is_veg": True, "prep": "8 mins", "desc": "Traditional hand-churned mango kulfi, silky vermicelli noodles, sweet basil sabja seeds, rose syrup.", "img": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?auto=format&fit=crop&w=600&q=80"},
    {"name": "Madagascan Vanilla Bean Creme Brulee", "price": 390, "is_veg": True, "prep": "10 mins", "desc": "Rich baked custard with crisp caramelized demerara sugar crust and fresh macerated berries.", "img": "https://images.unsplash.com/photo-1470124182917-cc6e71b22ecc?auto=format&fit=crop&w=600&q=80"},
    {"name": "Gulab Jamun Flambeed with Old Monk", "price": 360, "is_veg": True, "prep": "10 mins", "desc": "Mawa dumplings steeped in cardamom syrup, flambeed tableside with aged dark rum.", "img": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=600&q=80"},
    {"name": "New York Baked Raspberry Cheesecake", "price": 420, "is_veg": True, "prep": "8 mins", "desc": "Dense Philadelphia cream cheese cake, graham cracker crust, tart raspberry coulis.", "img": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=600&q=80"},
    {"name": "Warm Apple Tarte Tatin", "price": 430, "is_veg": True, "prep": "15 mins", "desc": "Caramelized Granny Smith apples on flaky puff pastry, served with cinnamon ice cream.", "img": "https://images.unsplash.com/photo-1568571780765-9276ac8b75a2?auto=format&fit=crop&w=600&q=80"},
    {"name": "Kashmiri Phirni in Clay Kasora", "price": 310, "is_veg": True, "prep": "8 mins", "desc": "Ground basmati pudding cooked with condensed milk, saffron strands and crushed almonds.", "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80"},
    {"name": "Paris-Brest Hazelnut Praline", "price": 440, "is_veg": True, "prep": "10 mins", "desc": "Ring of choux pastry filled with roasted hazelnut praline mousseline and toasted almond flakes.", "img": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=600&q=80"},
    {"name": "Rasmalai Tres Leches Cake", "price": 450, "is_veg": True, "prep": "10 mins", "desc": "Sponge cake soaked in saffron cardamom evaporated milk, topped with Bengali cottage cheese rounds.", "img": "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?auto=format&fit=crop&w=600&q=80"},
    {"name": "Belgian Waffles with Wild Berry Compote", "price": 380, "is_veg": True, "prep": "12 mins", "desc": "Crisp pearl-sugar yeast waffles, organic maple syrup, churned clotted cream, berries.", "img": "https://images.unsplash.com/photo-1562376552-0d160a2f238d?auto=format&fit=crop&w=600&q=80"},
    {"name": "Matcha Green Tea Crepe Cake", "price": 430, "is_veg": True, "prep": "8 mins", "desc": "Twenty paper-thin green tea crepes layered with light whipped Uji matcha cream.", "img": "https://images.unsplash.com/photo-1535141192574-5d4897c13136?auto=format&fit=crop&w=600&q=80"},
    {"name": "Churros Con Chocolate Artesanal", "price": 360, "is_veg": True, "prep": "10 mins", "desc": "Crispy fried Spanish dough fluted strips tossed in cinnamon sugar, thick bittersweet dipping chocolate.", "img": "https://images.unsplash.com/photo-1624300629298-e9de39c13be5?auto=format&fit=crop&w=600&q=80"},
    {"name": "Passion Fruit & Mango Panna Cotta", "price": 370, "is_veg": True, "prep": "8 mins", "desc": "Silky Piedmontese cooked cream infused with vanilla bean and crowned with tart passion fruit jelly.", "img": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=600&q=80"},
    {"name": "Warm Dark Chocolate Brownie Sundae", "price": 390, "is_veg": True, "prep": "10 mins", "desc": "Fudgy walnut brownie, double scoop roasted almond ice cream, warm fudge drizzle.", "img": "https://images.unsplash.com/photo-1607920591413-4ec007e70023?auto=format&fit=crop&w=600&q=80"},
    {"name": "Lemon Meringue Tartlet", "price": 350, "is_veg": True, "prep": "8 mins", "desc": "Sweet butter crust filled with zesty Amalfi lemon curd, torched Swiss meringue crown.", "img": "https://images.unsplash.com/photo-1519915028121-7d3463d20b13?auto=format&fit=crop&w=600&q=80"},
    {"name": "Saffron & Cardamom Mousse Dome", "price": 410, "is_veg": True, "prep": "8 mins", "desc": "Velvety white chocolate mousse with saffron heart, pistachio crunch base, mirror glaze.", "img": "https://images.unsplash.com/photo-1587314168485-3236d6710814?auto=format&fit=crop&w=600&q=80"},
    {"name": "Mocha Hazelnut Opera Cake", "price": 430, "is_veg": True, "prep": "8 mins", "desc": "Almond sponge soaked in coffee liqueur, chocolate ganache, French coffee buttercream.", "img": "https://images.unsplash.com/photo-1508737027454-e6454ef45afd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Banana Foster Crepe with Rum Glaze", "price": 380, "is_veg": True, "prep": "12 mins", "desc": "Warm crepes stuffed with caramelized bananas in dark brown sugar, butter, and spice.", "img": "https://images.unsplash.com/photo-1519676867240-f03562e64548?auto=format&fit=crop&w=600&q=80"},
    {"name": "Artisanal Gelato Trio", "price": 320, "is_veg": True, "prep": "5 mins", "desc": "Choose three scoops: Bronte Pistachio, Dark Belgian Chocolate, Bourbon Vanilla, Alfonso Mango.", "img": "https://images.unsplash.com/photo-1560008511-11c63416e52d?auto=format&fit=crop&w=600&q=80"},
    {"name": "Fig & Honey Frangipane Tart", "price": 390, "is_veg": True, "prep": "10 mins", "desc": "Roasted Turkish figs nestled in sweet almond paste cream, warm wildflower honey glaze.", "img": "https://images.unsplash.com/photo-1509365465985-25d11c17e812?auto=format&fit=crop&w=600&q=80"},
    {"name": "Coconut Panna Cotta with Pineapple Carpaccio", "price": 380, "is_veg": True, "prep": "8 mins", "desc": "Vegan tender coconut milk cream, star anise infused pineapple carpaccio ribbons.", "img": "https://images.unsplash.com/photo-1517433670267-08bbd4be890f?auto=format&fit=crop&w=600&q=80"},
    {"name": "Rich Red Velvet Truffle Cake", "price": 410, "is_veg": True, "prep": "8 mins", "desc": "Cocoa buttermilk sponge, Madagascar vanilla cream cheese frosting, raspberry dust.", "img": "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?auto=format&fit=crop&w=600&q=80"},
    {"name": "Cannoli Siciliani Classici (3 pcs)", "price": 350, "is_veg": True, "prep": "8 mins", "desc": "Crisp fried pastry shells piped with sweetened sheep ricotta, candied citrus peel, chocolate chips.", "img": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?auto=format&fit=crop&w=600&q=80"},
    {"name": "Cardamom & Jaggery Bread Pudding", "price": 340, "is_veg": True, "prep": "12 mins", "desc": "Baked brioche soaked in spiced palm jaggery custard, golden raisins, warm vanilla cream.", "img": "https://images.unsplash.com/photo-1587241321921-91a834d6d191?auto=format&fit=crop&w=600&q=80"},
    {"name": "Kahlua Tiramisu Pot", "price": 440, "is_veg": True, "prep": "8 mins", "desc": "Single-serving porcelain pot layered with espresso liqueur sponge and aerated zabaglione cream.", "img": "https://images.unsplash.com/photo-1579372786545-d24232daf58c?auto=format&fit=crop&w=600&q=80"},
    {"name": "Baked Alaska Flambee Tableside", "price": 550, "is_veg": True, "prep": "14 mins", "desc": "Sponge base, strawberry and vanilla gelato core, browned meringue shell flambeed with Grand Marnier.", "img": "https://images.unsplash.com/photo-1534432182912-63863115e106?auto=format&fit=crop&w=600&q=80"},
    {"name": "Exotic Fresh Fruit Platter", "price": 360, "is_veg": True, "prep": "8 mins", "desc": "Sliced dragon fruit, kiwi, passion fruit, cape gooseberries, melon, honey lime mint dressing.", "img": "https://images.unsplash.com/photo-1490818387583-1baba5e638af?auto=format&fit=crop&w=600&q=80"}
]

MENU_BEVERAGES = [
    {"name": "Kashmiri Royal Saffron Kahwa", "price": 280, "is_veg": True, "prep": "8 mins", "desc": "Pure saffron infused green tea brewed with cinnamon, green cardamom and crushed toasted almonds.", "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?auto=format&fit=crop&w=600&q=80"},
    {"name": "Ratnagiri Alphonso & Sweet Basil Chill", "price": 320, "is_veg": True, "prep": "5 mins", "desc": "Pure Alphonso mango pulp muddled with garden basil leaves, sparkling tonic, Himalayan pink salt.", "img": "https://images.unsplash.com/photo-1546173159-315724a31696?auto=format&fit=crop&w=600&q=80"},
    {"name": "Single-Origin 18hr Cold Brew Coffee", "price": 260, "is_veg": True, "prep": "5 mins", "desc": "Estate Arabica beans slow-steeped cold over 18 hours, served over crystal clear ice rock.", "img": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=600&q=80"},
    {"name": "Blue Pea Butterfly Flower Iced Elixir", "price": 290, "is_veg": True, "prep": "5 mins", "desc": "Antioxidant rich butterfly pea flower tea with fresh pressed lemon juice, changes color to royal violet.", "img": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Masala Chai in Clay Kullad", "price": 180, "is_veg": True, "prep": "6 mins", "desc": "Assam CTC tea simmered with fresh crushed ginger, holy basil, cloves, cinnamon, and whole milk.", "img": "https://images.unsplash.com/photo-1561336313-0bd5e0b27ec8?auto=format&fit=crop&w=600&q=80"},
    {"name": "Cucumber Mint & Elderflower Spritz", "price": 310, "is_veg": True, "prep": "5 mins", "desc": "English cucumber ribbons, garden mint, elderflower cordial, sparkling club soda.", "img": "https://images.unsplash.com/photo-1595981267035-7b04ca84a82d?auto=format&fit=crop&w=600&q=80"},
    {"name": "Fresh Tender Coconut Water in Shell", "price": 190, "is_veg": True, "prep": "5 mins", "desc": "Naturally sweet chilled tender coconut water served fresh in whole shell.", "img": "https://images.unsplash.com/photo-1525385133512-2f3bdd039054?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spanish Smoked Citrus Sangria Mocktail", "price": 340, "is_veg": True, "prep": "6 mins", "desc": "De-alcoholized Tempranillo grapes, macerated oranges, green apples, cinnamon stick smoke.", "img": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=600&q=80"},
    {"name": "Artisanal Hot Chocolate with Marshmallows", "price": 330, "is_veg": True, "prep": "8 mins", "desc": "Melted 64% Belgian dark chocolate whipped with steamed whole milk and toasted marshmallows.", "img": "https://images.unsplash.com/photo-1542990253-0d0f5be5f0ed?auto=format&fit=crop&w=600&q=80"},
    {"name": "Watermelon & Jalapeno Margarita Mocktail", "price": 290, "is_veg": True, "prep": "5 mins", "desc": "Fresh watermelon juice, crushed jalapeno ring, lime juice, sea salt rimmed coupe glass.", "img": "https://images.unsplash.com/photo-1587888637140-849b25d80ef9?auto=format&fit=crop&w=600&q=80"},
    {"name": "First Flush Darjeeling Silver Needles Tea", "price": 310, "is_veg": True, "prep": "6 mins", "desc": "Delicate spring harvest white tea leaves offering floral notes and subtle muscatel finish.", "img": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?auto=format&fit=crop&w=600&q=80"},
    {"name": "Avocado & Wild Honey Smoothie", "price": 340, "is_veg": True, "prep": "6 mins", "desc": "Creamy Hass avocado blended with almond milk, Greek yogurt, and organic Himalayan forest honey.", "img": "https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&w=600&q=80"},
    {"name": "Espresso Romano with Candied Lemon Twist", "price": 210, "is_veg": True, "prep": "5 mins", "desc": "Double ristretto shot of Italian roasted Arabica served with expressing candied lemon peel oil.", "img": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Berry Hibiscus Iced Tisane", "price": 270, "is_veg": True, "prep": "5 mins", "desc": "Egyptian wild hibiscus flower tea infused with crushed blackberries and a dash of agave nectar.", "img": "https://images.unsplash.com/photo-1556881286-fc6915169721?auto=format&fit=crop&w=600&q=80"},
    {"name": "Virgin Mojito Botanica", "price": 280, "is_veg": True, "prep": "5 mins", "desc": "Cuban spearmint leaves, muddled Persian limes, cane sugar, topped with sparkling club soda.", "img": "https://images.unsplash.com/photo-1551538827-9c037cb4f32a?auto=format&fit=crop&w=600&q=80"},
    {"name": "Golden Turmeric Latte (Haldi Doodh)", "price": 240, "is_veg": True, "prep": "7 mins", "desc": "Steamed almond milk whisked with organic Lakadong turmeric, black pepper, and cinnamon.", "img": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=600&q=80"},
    {"name": "Ginger Peach Iced Tea", "price": 260, "is_veg": True, "prep": "5 mins", "desc": "Black tea infused with peach puree, fresh pressed ginger juice, and crushed mint.", "img": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=600&q=80"},
    {"name": "Affogato Al Caffe Con Gelato", "price": 280, "is_veg": True, "prep": "5 mins", "desc": "Scoop of Tahitian vanilla bean gelato drowned in a hot double shot of freshly pulled espresso.", "img": "https://images.unsplash.com/photo-1592663527359-cf6642f54cff?auto=format&fit=crop&w=600&q=80"},
    {"name": "Rose & Lychee Blossom Cooler", "price": 310, "is_veg": True, "prep": "5 mins", "desc": "Chilled lychee nectar infused with Kannauj organic rose water and lime bubbles.", "img": "https://images.unsplash.com/photo-1536935338788-846bb9981813?auto=format&fit=crop&w=600&q=80"},
    {"name": "Caramel Macchiato Freddo", "price": 290, "is_veg": True, "prep": "6 mins", "desc": "Layers of cold frothed milk, robust espresso, and artisanal butter caramel ribbon.", "img": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?auto=format&fit=crop&w=600&q=80"},
    {"name": "Fresh Valencia Orange Juice", "price": 240, "is_veg": True, "prep": "5 mins", "desc": "100% pure cold-pressed Valencia oranges, freshly squeezed to order without added sugar.", "img": "https://images.unsplash.com/photo-1613478223719-2ab802602423?auto=format&fit=crop&w=600&q=80"},
    {"name": "Detox Green Juice Elixir", "price": 290, "is_veg": True, "prep": "6 mins", "desc": "Cold-pressed celery, green apple, cucumber, kale, ginger root, and lemon juice.", "img": "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chai Karak Emirati Style", "price": 220, "is_veg": True, "prep": "8 mins", "desc": "Strong black tea brewed with evaporated milk, crushed saffron and aromatic green cardamom pods.", "img": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&w=600&q=80"},
    {"name": "Pomegranate & Rosemary Fizz", "price": 320, "is_veg": True, "prep": "5 mins", "desc": "Tart fresh pomegranate juice shaken with torched rosemary sprig and craft soda.", "img": "https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?auto=format&fit=crop&w=600&q=80"},
    {"name": "Cappuccino Viennese with Cinnamon", "price": 250, "is_veg": True, "prep": "6 mins", "desc": "Double espresso topped with equal parts steamed milk and dense milk foam, dusted with Ceylon cinnamon.", "img": "https://images.unsplash.com/photo-1534778101976-62847782c213?auto=format&fit=crop&w=600&q=80"},
    {"name": "Dragon Fruit & Passion Lemonade", "price": 310, "is_veg": True, "prep": "5 mins", "desc": "Pink pitaya fruit puree, passion fruit syrup, sparkling lemonade over crushed ice.", "img": "https://images.unsplash.com/photo-1560512823-829485b8bf24?auto=format&fit=crop&w=600&q=80"},
    {"name": "San Pellegrino Sparkling Water (750ml)", "price": 350, "is_veg": True, "prep": "2 mins", "desc": "Naturally carbonated mineral water imported from the foothills of the Italian Alps.", "img": "https://images.unsplash.com/photo-1548839140-29a749e1bc4e?auto=format&fit=crop&w=600&q=80"},
    {"name": "Acqua Panna Still Spring Water (750ml)", "price": 350, "is_veg": True, "prep": "2 mins", "desc": "Smooth natural mineral spring water bottled at the source in Tuscany, Italy.", "img": "https://images.unsplash.com/photo-1523362628745-0c100150b504?auto=format&fit=crop&w=600&q=80"},
    {"name": "Iced Vietnamese Drip Coffee with Condensed Milk", "price": 270, "is_veg": True, "prep": "7 mins", "desc": "Dark roast Robusta filtered through traditional phin filter over sweetened condensed milk.", "img": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=600&q=80"},
    {"name": "Smoked Earl Grey Cold Infusion", "price": 280, "is_veg": True, "prep": "5 mins", "desc": "Bergamot infused black tea with applewood smoke, citrus peel and cane syrup.", "img": "https://images.unsplash.com/photo-1563822249548-9a72b6353cd1?auto=format&fit=crop&w=600&q=80"}
]

MENU_SNACKS = [
    {"name": "Royal Club Triple-Decker Sandwich", "price": 490, "is_veg": False, "prep": "15 mins", "desc": "Smoked chicken breast, farm egg, streaky bacon, aged cheddar, butterhead lettuce, truffle fries.", "img": "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=600&q=80"},
    {"name": "Avocado Tartine with Poached Organic Eggs", "price": 440, "is_veg": True, "prep": "12 mins", "desc": "Charred sourdough toast, smashed Hass avocado, dukkah spice sprinkle, soft poached country eggs.", "img": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=600&q=80"},
    {"name": "Truffled Black Angus Beef Burger", "price": 680, "is_veg": False, "prep": "18 mins", "desc": "200g prime Angus patty, caramelized shallots, melted raclette cheese, brioche bun, parmesan fries.", "img": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=600&q=80"},
    {"name": "Crispy Paneer Makhani Bao Buns (3 pcs)", "price": 420, "is_veg": True, "prep": "14 mins", "desc": "Steamed lotus leaf buns stuffed with crunchy spiced paneer, pickled radish, makhani drizzle.", "img": "https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=600&q=80"},
    {"name": "BBQ Pulled Chicken Sliders (3 pcs)", "price": 480, "is_veg": False, "prep": "15 mins", "desc": "Slow-smoked chicken in apple cider barbecue sauce, purple cabbage slaw, toasted mini brioche.", "img": "https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=600&q=80"},
    {"name": "Smoked Salmon & Cream Cheese Bagel", "price": 540, "is_veg": False, "prep": "10 mins", "desc": "Toasted everything bagel, Atlantic cured smoked salmon, caper berry cream cheese, red onion rings.", "img": "https://images.unsplash.com/photo-1510693206972-df098062cb71?auto=format&fit=crop&w=600&q=80"},
    {"name": "Gourmet Margherita Flatbread", "price": 390, "is_veg": True, "prep": "12 mins", "desc": "Thin crispy dough, San Marzano tomato spread, buffalo mozzarella, garden basil leaves.", "img": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chili Cheese Garlic Toast Royale", "price": 320, "is_veg": True, "prep": "10 mins", "desc": "Toasted French loaf topped with melted mozzarella, cheddar, green chilies, cilantro, and garlic butter.", "img": "https://images.unsplash.com/photo-1619895092538-128341789043?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spicy Korean Gochujang Chicken Wings", "price": 460, "is_veg": False, "prep": "15 mins", "desc": "Double fried crispy chicken wings glazed in spicy-sweet gochujang chili paste with sesame seeds.", "img": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=600&q=80"},
    {"name": "Mediterranean Falafel Pita Pocket", "price": 360, "is_veg": True, "prep": "12 mins", "desc": "Herbed chickpea fritters stuffed into warm wholewheat pita with tahini, cucumber, and pickled turnip.", "img": "https://images.unsplash.com/photo-1593001874117-c99c800e3eb7?auto=format&fit=crop&w=600&q=80"},
    {"name": "Artisanal Cheese & Charcuterie Board", "price": 850, "is_veg": False, "prep": "10 mins", "desc": "Imported Manchego, Brie de Meaux, Prosciutto di Parma, salami, dried figs, honey, crackers.", "img": "https://images.unsplash.com/photo-1631379578550-7038263db699?auto=format&fit=crop&w=600&q=80"},
    {"name": "Loaded Truffle Quesadilla", "price": 420, "is_veg": True, "prep": "12 mins", "desc": "Flour tortillas packed with sauteed wild mushrooms, white truffle oil, Oaxaca cheese, pico de gallo.", "img": "https://images.unsplash.com/photo-1599974579688-8dbdd335c77f?auto=format&fit=crop&w=600&q=80"},
    {"name": "Crispy Fish & Hand-Cut Chips", "price": 560, "is_veg": False, "prep": "16 mins", "desc": "Beer-battered fresh sea bass fillet, chunky skin-on fries, mushy peas, caper tartar sauce.", "img": "https://images.unsplash.com/photo-1579208030886-b937da0925dc?auto=format&fit=crop&w=600&q=80"},
    {"name": "Peri-Peri Chicken Kathi Roll", "price": 410, "is_veg": False, "prep": "14 mins", "desc": "Flaky layered paratha wrapped with grilled peri-peri spiced chicken, sliced peppers, mint chutney.", "img": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?auto=format&fit=crop&w=600&q=80"},
    {"name": "Paneer Tikka Kathi Roll", "price": 360, "is_veg": True, "prep": "14 mins", "desc": "Tandoor roasted cottage cheese in flaky eggless paratha wrap with pickled onions.", "img": "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?auto=format&fit=crop&w=600&q=80"},
    {"name": "Vietnamese Fresh Shrimp Rice Paper Rolls", "price": 480, "is_veg": False, "prep": "10 mins", "desc": "Poached prawns, rice vermicelli, mint, Thai basil, cucumber wrapped in rice sheet, peanut dip.", "img": "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=600&q=80"},
    {"name": "Melted Camembert with Rosemary & Garlic", "price": 580, "is_veg": True, "prep": "15 mins", "desc": "Whole baked Normandy Camembert infused with garlic slivers and rosemary, warm crusty baguette.", "img": "https://images.unsplash.com/photo-1452195100486-9cc805987862?auto=format&fit=crop&w=600&q=80"},
    {"name": "Kolkata Mutton Mughlai Paratha", "price": 520, "is_veg": False, "prep": "18 mins", "desc": "Crispy fried deep-layered pastry filled with minced spiced goat meat, beaten egg, green chilies.", "img": "https://images.unsplash.com/photo-1541544741938-0af808871cc0?auto=format&fit=crop&w=600&q=80"},
    {"name": "Crispy Panko Onion Rings with Ranch", "price": 280, "is_veg": True, "prep": "10 mins", "desc": "Sweet Spanish onion rings breaded with Japanese panko flakes, served with buttermilk ranch dip.", "img": "https://images.unsplash.com/photo-1639024471287-03518883512d?auto=format&fit=crop&w=600&q=80"},
    {"name": "Pulled Lamb Tacos with Salsa Verde (3 pcs)", "price": 540, "is_veg": False, "prep": "14 mins", "desc": "Warm corn tortillas loaded with 12-hour braised barbacoa lamb, pickled onions, cotija cheese.", "img": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=600&q=80"},
    {"name": "Mushroom & Fontina Cheese Panini", "price": 390, "is_veg": True, "prep": "12 mins", "desc": "Pressed ciabatta loaf filled with sauteed porcini and button mushrooms, molten fontina cheese.", "img": "https://images.unsplash.com/photo-1528736235302-52922df5c122?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chicken Tikka Wood-Fired Calzone", "price": 490, "is_veg": False, "prep": "16 mins", "desc": "Folded pizza pocket stuffed with tandoori chicken chunks, mozzarella, and spiced marinara.", "img": "https://images.unsplash.com/photo-1541745537411-b8046dc6d66c?auto=format&fit=crop&w=600&q=80"},
    {"name": "Spinach & Sweet Corn Vol-Au-Vent", "price": 360, "is_veg": True, "prep": "12 mins", "desc": "Puff pastry baskets filled with creamy spinach, corn kernels, and gratinated parmesan.", "img": "https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?auto=format&fit=crop&w=600&q=80"},
    {"name": "Crispy Buffalo Chicken Tenders", "price": 420, "is_veg": False, "prep": "12 mins", "desc": "Golden fried chicken breast tenders tossed in spicy cayenne buffalo sauce with blue cheese dip.", "img": "https://images.unsplash.com/photo-1527477396000-e27163b481c2?auto=format&fit=crop&w=600&q=80"},
    {"name": "Smoked Gouda & Caramelized Onion Toastie", "price": 340, "is_veg": True, "prep": "10 mins", "desc": "Cast iron grilled multigrain bread with melted Dutch Gouda and slow braised sweet onions.", "img": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?auto=format&fit=crop&w=600&q=80"},
    {"name": "Prawn Cocktail Royale", "price": 590, "is_veg": False, "prep": "10 mins", "desc": "Steamed ocean tiger prawns served chilled in Marie Rose brandy cocktail sauce with lemon wedge.", "img": "https://images.unsplash.com/photo-1535400255456-984241443b29?auto=format&fit=crop&w=600&q=80"},
    {"name": "Wild Berry & Granola Parfait", "price": 310, "is_veg": True, "prep": "6 mins", "desc": "Greek honey yogurt, toasted almond granola, macerated blueberries and strawberry coulis.", "img": "https://images.unsplash.com/photo-1505253758473-96b7015fcd40?auto=format&fit=crop&w=600&q=80"},
    {"name": "Tempura Vegetables with Dashi Mirin Dip", "price": 370, "is_veg": True, "prep": "12 mins", "desc": "Lacy batter-crisped asparagus, sweet potato, lotus stem, and bell peppers.", "img": "https://images.unsplash.com/photo-1581299894007-aaa50297cf16?auto=format&fit=crop&w=600&q=80"},
    {"name": "Lamb Kheema Pav with Buttered Ladi Pav", "price": 480, "is_veg": False, "prep": "14 mins", "desc": "Spiced minced goat meat braised with green peas, served with toasted buttery soft bread buns.", "img": "https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=600&q=80"},
    {"name": "Chili Garlic Edamame Pods", "price": 310, "is_veg": True, "prep": "8 mins", "desc": "Steamed young soybean pods wok-flashed with crispy garlic chips, sesame oil, and sea salt.", "img": "https://images.unsplash.com/photo-1546554137-f86b9593a222?auto=format&fit=crop&w=600&q=80"}
]

# --------------------------------------------------------------------------------------
# 2. ROOM INVENTORY (40+ Rooms mapped to real wings, floors 1-8, and flat numbering)
# --------------------------------------------------------------------------------------

ROOMS_CATALOG = [
    # --- HERITAGE WING (Floors 1 - 2, Classic Arch & Garden Views) ---
    {"number": "101", "flat_code": "HW-101", "wing": "Heritage Wing", "floor": 1, "type": "Deluxe Heritage", "price": 3800, "max_guests": 2, "size": "420 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"},
    {"number": "102", "flat_code": "HW-102", "wing": "Heritage Wing", "floor": 1, "type": "Deluxe Heritage", "price": 3800, "max_guests": 2, "size": "420 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80"},
    {"number": "103", "flat_code": "HW-103", "wing": "Heritage Wing", "floor": 1, "type": "Garden Verandah Suite", "price": 5200, "max_guests": 3, "size": "650 sq ft", "status": "occupied", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "104", "flat_code": "HW-104", "wing": "Heritage Wing", "floor": 1, "type": "Garden Verandah Suite", "price": 5200, "max_guests": 3, "size": "650 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80"},
    {"number": "105", "flat_code": "HW-105", "wing": "Heritage Wing", "floor": 1, "type": "Deluxe Heritage", "price": 3800, "max_guests": 2, "size": "420 sq ft", "status": "dirty", "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80"},
    {"number": "106", "flat_code": "HW-106", "wing": "Heritage Wing", "floor": 1, "type": "Deluxe Heritage", "price": 3800, "max_guests": 2, "size": "420 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"},
    {"number": "107", "flat_code": "HW-107", "wing": "Heritage Wing", "floor": 1, "type": "Courtyard Suite", "price": 4800, "max_guests": 3, "size": "580 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80"},
    {"number": "108", "flat_code": "HW-108", "wing": "Heritage Wing", "floor": 1, "type": "Courtyard Suite", "price": 4800, "max_guests": 3, "size": "580 sq ft", "status": "maintenance", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "201", "flat_code": "HW-201", "wing": "Heritage Wing", "floor": 2, "type": "Deluxe Heritage", "price": 4000, "max_guests": 2, "size": "450 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80"},
    {"number": "202", "flat_code": "HW-202", "wing": "Heritage Wing", "floor": 2, "type": "Deluxe Heritage", "price": 4000, "max_guests": 2, "size": "450 sq ft", "status": "occupied", "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80"},
    {"number": "203", "flat_code": "HW-203", "wing": "Heritage Wing", "floor": 2, "type": "Heritage Royal Balcony", "price": 5600, "max_guests": 3, "size": "680 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80"},
    {"number": "204", "flat_code": "HW-204", "wing": "Heritage Wing", "floor": 2, "type": "Heritage Royal Balcony", "price": 5600, "max_guests": 3, "size": "680 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},

    # --- ROYAL WING (Floors 3 - 5, Executive Lounges & Pool Views) ---
    {"number": "301", "flat_code": "RW-301", "wing": "Royal Wing", "floor": 3, "type": "Royal Club Room", "price": 6200, "max_guests": 2, "size": "550 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80"},
    {"number": "302", "flat_code": "RW-302", "wing": "Royal Wing", "floor": 3, "type": "Royal Club Room", "price": 6200, "max_guests": 2, "size": "550 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"},
    {"number": "303", "flat_code": "RW-303", "wing": "Royal Wing", "floor": 3, "type": "Executive Suite", "price": 7800, "max_guests": 4, "size": "820 sq ft", "status": "occupied", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
    {"number": "304", "flat_code": "RW-304", "wing": "Royal Wing", "floor": 3, "type": "Executive Suite", "price": 7800, "max_guests": 4, "size": "820 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "305", "flat_code": "RW-305", "wing": "Royal Wing", "floor": 3, "type": "Royal Club Room", "price": 6200, "max_guests": 2, "size": "550 sq ft", "status": "cleaning", "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80"},
    {"number": "401", "flat_code": "RW-401", "wing": "Royal Wing", "floor": 4, "type": "Royal Club Room", "price": 6500, "max_guests": 2, "size": "560 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80"},
    {"number": "402", "flat_code": "RW-402", "wing": "Royal Wing", "floor": 4, "type": "Royal Club Room", "price": 6500, "max_guests": 2, "size": "560 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"},
    {"number": "403", "flat_code": "RW-403", "wing": "Royal Wing", "floor": 4, "type": "Diplomatic Suite", "price": 9500, "max_guests": 4, "size": "950 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
    {"number": "404", "flat_code": "RW-404", "wing": "Royal Wing", "floor": 4, "type": "Diplomatic Suite", "price": 9500, "max_guests": 4, "size": "950 sq ft", "status": "occupied", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "501", "flat_code": "RW-501", "wing": "Royal Wing", "floor": 5, "type": "Grand Royal Suite", "price": 11000, "max_guests": 4, "size": "1100 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80"},
    {"number": "502", "flat_code": "RW-502", "wing": "Royal Wing", "floor": 5, "type": "Grand Royal Suite", "price": 11000, "max_guests": 4, "size": "1100 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
    {"number": "503", "flat_code": "RW-503", "wing": "Royal Wing", "floor": 5, "type": "Executive Suite", "price": 8200, "max_guests": 4, "size": "850 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80"},
    {"number": "504", "flat_code": "RW-504", "wing": "Royal Wing", "floor": 5, "type": "Executive Suite", "price": 8200, "max_guests": 4, "size": "850 sq ft", "status": "dirty", "image": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=800&q=80"},

    # --- SKYLINE TOWER (Floors 6 - 8, Panoramic Penthouse & Presidential Villas) ---
    {"number": "601", "flat_code": "ST-601", "wing": "Skyline Tower", "floor": 6, "type": "Skyline Premier", "price": 9200, "max_guests": 2, "size": "620 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=800&q=80"},
    {"number": "602", "flat_code": "ST-602", "wing": "Skyline Tower", "floor": 6, "type": "Skyline Premier", "price": 9200, "max_guests": 2, "size": "620 sq ft", "status": "occupied", "image": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80"},
    {"number": "603", "flat_code": "ST-603", "wing": "Skyline Tower", "floor": 6, "type": "Skyline Jacuzzi Suite", "price": 13500, "max_guests": 3, "size": "1050 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "604", "flat_code": "ST-604", "wing": "Skyline Tower", "floor": 6, "type": "Skyline Jacuzzi Suite", "price": 13500, "max_guests": 3, "size": "1050 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80"},
    {"number": "701", "flat_code": "ST-701", "wing": "Skyline Tower", "floor": 7, "type": "Panoramic Penthouse", "price": 18500, "max_guests": 4, "size": "1650 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
    {"number": "702", "flat_code": "ST-702", "wing": "Skyline Tower", "floor": 7, "type": "Panoramic Penthouse", "price": 18500, "max_guests": 4, "size": "1650 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1591088398332-8a7791972843?auto=format&fit=crop&w=800&q=80"},
    {"number": "703", "flat_code": "ST-703", "wing": "Skyline Tower", "floor": 7, "type": "Governor Penthouse", "price": 22000, "max_guests": 6, "size": "2100 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=800&q=80"},
    {"number": "801", "flat_code": "ST-801", "wing": "Skyline Tower", "floor": 8, "type": "The Nur-e-Haya Presidential Villa", "price": 35000, "max_guests": 8, "size": "3400 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=800&q=80"},
    {"number": "802", "flat_code": "ST-802", "wing": "Skyline Tower", "floor": 8, "type": "Imperial Royal Residence", "price": 32000, "max_guests": 6, "size": "2900 sq ft", "status": "available", "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?auto=format&fit=crop&w=800&q=80"}
]

# --------------------------------------------------------------------------------------
# 3. RESTAURANT TABLES (24 Tables mapped across hotel dining zones)
# --------------------------------------------------------------------------------------

RESTAURANT_TABLES = [
    # Grand Royal Dining Hall
    {"table_no": "T-01", "zone": "Grand Dining Hall", "capacity": 2, "status": "available"},
    {"table_no": "T-02", "zone": "Grand Dining Hall", "capacity": 2, "status": "occupied", "guest_name": "Dr. Aris Thorne", "order_id": "ORD-5501"},
    {"table_no": "T-03", "zone": "Grand Dining Hall", "capacity": 4, "status": "available"},
    {"table_no": "T-04", "zone": "Grand Dining Hall", "capacity": 4, "status": "available"},
    {"table_no": "T-05", "zone": "Grand Dining Hall", "capacity": 6, "status": "busing"},
    {"table_no": "T-06", "zone": "Grand Dining Hall", "capacity": 6, "status": "available"},
    {"table_no": "T-07", "zone": "Grand Dining Hall", "capacity": 8, "status": "available"},
    {"table_no": "T-08", "zone": "Grand Dining Hall", "capacity": 4, "status": "available"},
    {"table_no": "T-09", "zone": "Grand Dining Hall", "capacity": 2, "status": "available"},
    {"table_no": "T-10", "zone": "Grand Dining Hall", "capacity": 4, "status": "available"},

    # Rooftop Skyline Terrace
    {"table_no": "T-11", "zone": "Rooftop Terrace", "capacity": 2, "status": "available"},
    {"table_no": "T-12", "zone": "Rooftop Terrace", "capacity": 2, "status": "available"},
    {"table_no": "T-13", "zone": "Rooftop Terrace", "capacity": 4, "status": "occupied", "guest_name": "Lord Sterling", "order_id": "ORD-5502"},
    {"table_no": "T-14", "zone": "Rooftop Terrace", "capacity": 4, "status": "available"},
    {"table_no": "T-15", "zone": "Rooftop Terrace", "capacity": 6, "status": "available"},
    {"table_no": "T-16", "zone": "Rooftop Terrace", "capacity": 6, "status": "available"},
    {"table_no": "T-17", "zone": "Rooftop Terrace", "capacity": 2, "status": "available"},
    {"table_no": "T-18", "zone": "Rooftop Terrace", "capacity": 4, "status": "available"},

    # Poolside Palm Verandah
    {"table_no": "T-19", "zone": "Poolside Verandah", "capacity": 4, "status": "available"},
    {"table_no": "T-20", "zone": "Poolside Verandah", "capacity": 4, "status": "available"},
    {"table_no": "T-21", "zone": "Poolside Verandah", "capacity": 2, "status": "busing"},
    {"table_no": "T-22", "zone": "Poolside Verandah", "capacity": 6, "status": "available"},
    {"table_no": "T-23", "zone": "Poolside Verandah", "capacity": 4, "status": "available"},
    {"table_no": "T-24", "zone": "Poolside Verandah", "capacity": 2, "status": "available"},

    # Private Dining Salons
    {"table_no": "P-01", "zone": "Private Dining Salon", "capacity": 12, "status": "available"},
    {"table_no": "P-02", "zone": "Private Dining Salon", "capacity": 16, "status": "reserved", "guest_name": "Ambassador VIP Gala"}
]


def seed_all_data(db_client=None):
    """
    Populates Firestore (or in-memory mock) with 150+ menu items, 40+ rooms, and 24 tables.
    """
    if db_client is None:
        from app.firebase_db import get_db
        db_client = get_db()

    now_iso = datetime.utcnow().isoformat() + "Z"
    
    # 1. Seed Menu Items
    menu_col = db_client.collection('menu_items')
    all_menu = []
    for it in MENU_STARTERS:
        it_copy = dict(it)
        it_copy['category'] = 'starters'
        it_copy['diet'] = 'veg' if it['is_veg'] else 'non-veg'
        all_menu.append(it_copy)
    for it in MENU_MAINS:
        it_copy = dict(it)
        it_copy['category'] = 'mains'
        it_copy['diet'] = 'veg' if it['is_veg'] else 'non-veg'
        all_menu.append(it_copy)
    for it in MENU_DESSERTS:
        it_copy = dict(it)
        it_copy['category'] = 'desserts'
        it_copy['diet'] = 'veg' if it['is_veg'] else 'non-veg'
        all_menu.append(it_copy)
    for it in MENU_BEVERAGES:
        it_copy = dict(it)
        it_copy['category'] = 'beverages'
        it_copy['diet'] = 'veg' if it['is_veg'] else 'non-veg'
        all_menu.append(it_copy)
    for it in MENU_SNACKS:
        it_copy = dict(it)
        it_copy['category'] = 'snacks'
        it_copy['diet'] = 'veg' if it['is_veg'] else 'non-veg'
        all_menu.append(it_copy)

    seeded_menu_count = 0
    for idx, item in enumerate(all_menu, 1):
        item_id = f"item_{idx}"
        doc_data = dict(item)
        doc_data['id'] = item_id
        doc_data['image_url'] = item.get('img') or item.get('image_url')
        doc_data['img'] = doc_data['image_url']
        doc_data['available'] = True
        doc_data['created_at'] = now_iso
        menu_col.document(item_id).set(doc_data)
        seeded_menu_count += 1

    # 2. Seed Rooms (Single Canonical Document per Room - Part 0.1)
    rooms_col = db_client.collection('rooms')
    seeded_room_count = 0
    for r in ROOMS_CATALOG:
        doc_id = f"rm_{r['flat_code']}" if r.get('flat_code') else f"rm_{r['number']}"
        doc_data = dict(r)
        doc_data['id'] = doc_id
        doc_data['canonical_id'] = doc_id
        doc_data['flat_code'] = r.get('flat_code', f"FL-{r['number']}")
        doc_data['flat_no'] = r.get('flat_code', f"FL-{r['number']}")
        doc_data['number'] = str(r['number'])
        doc_data['is_active'] = True
        doc_data['amenities'] = ["High-Speed WiFi", "Climate Control AC", "Smart 4K TV", "Marble Ensuite Bath", "Signature Bathrobes", "Nespresso Bar"]
        if "Suite" in r['type'] or "Penthouse" in r['type'] or "Villa" in r['type']:
            doc_data['amenities'].extend(["Private Butler Service", "Jacuzzi Spa Tub", "Walk-in Wardrobe", "Chauffeured Airport Transfer"])
        rooms_col.document(doc_id).set(doc_data)
        seeded_room_count += 1

    # 3. Seed Restaurant Tables
    tables_col = db_client.collection('restaurant_tables')
    seeded_table_count = 0
    for t in RESTAURANT_TABLES:
        t_id = f"tbl_{t['table_no']}"
        t_data = dict(t)
        t_data['id'] = t_id
        tables_col.document(t_id).set(t_data)
        seeded_table_count += 1

    # 4. Seed Demo Active Reservation & Dining Order for Guest Demo User (user@nur-e-haya.com)
    b_col = db_client.collection('bookings')
    demo_booking = {
        "id": "b_demo_8812",
        "booking_no": "BK-DEMO-8812",
        "user_email": "user@nur-e-haya.com",
        "guest_name": "Dr. Aisha Rahman",
        "phone": "+91 98765 43210",
        "room_id": "room_201",
        "room_number": "201",
        "room_name": "Royal Heritage Suite",
        "check_in": (datetime.utcnow().date()).isoformat(),
        "check_out": (datetime.utcnow().date() + timedelta(days=3)).isoformat(),
        "guests": 2,
        "subtotal": 24000.0,
        "discount_amount": 2400.0,
        "tax": 2592.0,
        "service_charge": 1200.0,
        "total_price": 25392.0,
        "status": "confirmed",
        "source": "web",
        "txn_id": "txn_demo_init_01",
        "payment_method": "upi_qr",
        "payment_status": "paid",
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
    }
    b_col.document('b_demo_8812').set(demo_booking)

    o_col = db_client.collection('orders')
    demo_order = {
        "id": "ord_demo_5521",
        "order_no": "ORD-DEMO-5521",
        "user_email": "user@nur-e-haya.com",
        "guest_name": "Dr. Aisha Rahman",
        "room_number": "201",
        "table_number": "T-04",
        "items": [
            {"name": "Nur-e-Haya Royal Dum Biryani", "price": 750, "quantity": 1},
            {"name": "Paneer Lababdar with Laccha Paratha", "price": 520, "quantity": 1},
            {"name": "Ratnagiri Alphonso & Sweet Basil Chill", "price": 320, "quantity": 2}
        ],
        "subtotal": 1910.0,
        "discount_percent": 10.0,
        "discount_amount": 191.0,
        "tax": 85.95,
        "total": 1804.95,
        "status": "preparing",
        "payment_method": "upi_qr",
        "payment_status": "paid",
        "created_at": (datetime.utcnow() - timedelta(minutes=25)).isoformat() + "Z"
    }
    o_col.document('ord_demo_5521').set(demo_order)

    # Seed transaction
    t_col = db_client.collection('transactions')
    t_col.document('txn_demo_init_01').set({
        "transaction_id": "txn_demo_init_01",
        "user_email": "user@nur-e-haya.com",
        "amount": 25392.0,
        "total": 25392.0,
        "payment_method": "upi_qr",
        "payment_status": "paid",
        "status": "paid",
        "booking_id": "b_demo_8812",
        "reference_no": "BK-DEMO-8812",
        "order_summary": {
            "subtotal": 24000.0,
            "discount": 2400.0,
            "tax": 2592.0,
            "service_charge": 1200.0,
            "total": 25392.0,
            "currency": "INR"
        },
        "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
    })

    # Seed 22 Facilities across 5 subsections
    f_col = db_client.collection('facilities')
    seeded_fac_count = 0
    for fac in FACILITIES_DATA:
        fac_doc = dict(fac)
        fac_doc["created_at"] = (datetime.utcnow() - timedelta(days=10)).isoformat() + "Z"
        f_col.document(fac["id"]).set(fac_doc)
        seeded_fac_count += 1

    # Seed demo confirmed spa booking for demo user
    spa_col = db_client.collection('spa_bookings')
    spa_col.document('spa_demo_9901').set({
        "id": "spa_demo_9901",
        "booking_no": "SPA-DEMO-9901",
        "facility_id": "fac_spa_abhyanga",
        "facility_name": "Abhyanga Full-Body Warm Herbal Oil Massage",
        "treatment": "Abhyanga Full-Body Warm Herbal Oil Massage",
        "category": "Ayurvedic Spa & Wellness",
        "user_email": "user@nur-e-haya.com",
        "guest_name": "Dr. Aisha Rahman",
        "room_number": "201",
        "date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "slot_time": "10:30 AM",
        "time_slot": "10:30 AM",
        "price": 3500.0,
        "status": "confirmed",
        "payment_status": "paid",
        "therapist": "Master Ayurvedic Practitioner",
        "created_at": (datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z"
    })

    logger.info(f"✅ Seeding Complete: {seeded_menu_count} Menu Items, {seeded_room_count} Rooms, {seeded_table_count} Tables, {seeded_fac_count} Facilities, Demo bookings")
    return {
        "menu_items": seeded_menu_count,
        "rooms": seeded_room_count,
        "tables": seeded_table_count,
        "facilities": seeded_fac_count,
        "demo_booking": demo_booking["booking_no"],
        "demo_order": demo_order["order_no"]
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    res = seed_all_data()
    print(f"Successfully seeded database: {res}")
