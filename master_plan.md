# Nur-e-Haya — Industry-Ready Hotel Management System

> Comprehensive master plan for transforming the college-level hotel booking app into a fully digital, industry-ready hotel operating platform: 90 screens across 13 modules, serving every real hotel department — front office, housekeeping, kitchen, engineering, concierge, accounts, events, wellness, security, and management.

---

## 1. Project Vision

One platform, every hotel department, fully digital:

- **Guests (Users & Members)** — discover rooms, book, check-in, dine, order room service, request services, pay by QR, write reviews, earn loyalty points. Members get 5% off everything.
- **Front Desk** — walk-ins, check-in/out, room status board, guest history, night audit.
- **Housekeeping / Laundry / Maintenance Staff** — priority-sorted task queues, room status updates, lost & found, linen tracking.
- **Chefs & Kitchen** — live order queue (received → preparing → ready → served), inventory with low-stock alerts.
- **Concierge** — wake-up calls, taxis, airport transfers, tours, doctor on call.
- **Accountant / Cashier** — transactions, invoices, refunds, daily settlement.
- **Manager** — operations dashboard, task assignment, room/rate management, reports, broadcasts.
- **Admin** — full analytics, user/role management, menu & catalogue CRUD, QR verification, audit logs, settings, backup/export.

**Design language** — Google apps colours (Blue `#4285F4`, Red `#EA4335`, Yellow `#FBBC05`, Green `#34A853`) with Apple-style UI: system font stack, light surfaces on `#F5F5F7`, large rounded cards (16–22px), soft elevation, generous whitespace, symbol-style icons.

---

## 2. Product Modules

| # | Module | Department | Purpose |
|---|---|---|---|
| 1 | Auth & Onboarding | IT / All | Register (OTP), login, SSO, role routing |
| 2 | Common | All | Profile, notifications, search, chatbot, help |
| 3 | Front Office | Front Desk | Booking, check-in/out, room board, night audit |
| 4 | Dining & Room Service | F&B / Kitchen | Menus, cart, orders, kitchen queue, mini bar |
| 5 | Housekeeping & Guest Services | Housekeeping | Task board, service requests, lost & found, linen |
| 6 | Engineering / Maintenance | Maintenance | Work orders, preventive calendar, assets |
| 7 | Concierge | Concierge | Transfers, tours, doctor, local guide |
| 8 | Accounts & Payments | Accounts | Ledger, invoices, QR verify, refunds, settlement |
| 9 | Events, Banquets & Wellness | Events / Spa | Halls, catering, spa, pool, gym |
| 10 | Manager / Operations | Management | Dashboard, task assignment, rates, reports |
| 11 | Admin / Platform | IT | Analytics, CRUD consoles, audit, settings |
| 12 | Security, Parking & Safety | Security | Visitor log, incidents, parking, emergency |
| 13 | CRM, Loyalty & Marketing | Marketing | Loyalty, memberships, reviews, campaigns |

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask 3 (blueprint architecture) |
| Database | Firebase Firestore (existing) |
| Auth | bcrypt (existing) + server-generated OTP + Google OAuth (existing) |
| QR | Python `qrcode` + `Pillow` |
| Charts | Chart.js (CDN) |
| Frontend | Jinja2 + vanilla JS; Google Material × Apple design system |
| Deployment | Render (existing `render.yaml`, `Procfile`, `runtime.txt`) |

New dependencies: `qrcode==7.4.2`, `Pillow`.

---

## 4. Roles & Permissions Matrix

| Module | User | Member | Front Desk | Housekeeping | Laundry | Maintenance | Chef | Waiter/ Cashier | Concierge | Accountant | Manager | Admin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Auth & Onboarding | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Front Office (book, check-in/out) | ✅ | ✅ | ✅ manage | – | – | – | – | – | – | ✅ view | ✅ manage | ✅ manage |
| Dining & Room Service | ✅ | ✅ | – | – | – | – | ✅ fulfill | ✅ serve | – | ✅ view | ✅ view | ✅ manage menu |
| Housekeeping & Services | ✅ request | ✅ request | ✅ assign | ✅ fulfill | ✅ fulfill | ✅ fulfill | – | – | – | – | ✅ oversee | ✅ oversee |
| Engineering / Maintenance | ✅ report | ✅ report | ✅ log | – | – | ✅ fulfill | – | – | – | – | ✅ oversee | ✅ oversee |
| Concierge | ✅ request | ✅ request | ✅ assign | – | – | – | – | – | ✅ fulfill | – | ✅ oversee | ✅ oversee |
| Accounts & Payments | ✅ own txns | ✅ own txns | ✅ collect | – | – | – | – | ✅ take pay | – | ✅ ledger | ✅ view | ✅ full |
| Events & Wellness | ✅ book | ✅ book | ✅ assist | – | – | – | – | – | ✅ assist | ✅ invoice | ✅ manage | ✅ manage |
| Manager / Operations | – | – | – | – | – | – | – | – | – | – | ✅ | ✅ full |
| Admin / Platform | – | – | – | – | – | – | – | – | – | – | partial | ✅ |
| Security & Parking | – | – | ✅ log | – | – | – | – | – | – | – | ✅ view | ✅ view |
| CRM, Loyalty & Marketing | ✅ earn | ✅ earn | – | – | – | – | – | – | – | – | ✅ manage | ✅ manage |

**Roles**: `user`, `member` (5% discount + loyalty), staff roles `front_desk | housekeeping | laundry | maintenance | chef | waiter | concierge | security`, plus `accountant`, `manager`, `admin`, `super_admin`.

### Seed accounts (created in Phase 2) — password `Hotel@123`
| Email | Role | Staff role |
|---|---|---|
| admin@nur-e-haya.com | admin | – |
| manager@nur-e-haya.com | manager | – |
| chef@nur-e-haya.com | chef | – |
| frontdesk@nur-e-haya.com | staff | front_desk |
| cleaning@nur-e-haya.com | staff | housekeeping |
| laundry@nur-e-haya.com | staff | laundry |
| maintenance@nur-e-haya.com | staff | maintenance |
| concierge@nur-e-haya.com | staff | concierge |
| accountant@nur-e-haya.com | accountant | – |
| member@nur-e-haya.com | member | – |
| user@nur-e-haya.com | user | – |

---

## 5. Feature Set by Module

**1. Auth & Onboarding** — register (name/email/phone/password + role), OTP verify (6-digit, bcrypt-hashed, 5-min expiry, 5 attempts, purposes: register/reset/checkin), login, Google SSO, logout, forgot/reset password, role-routed dashboard, seed accounts.

**2. Common** — profile & settings, notifications center, global search (guests/rooms/bookings/orders), AI chatbot (reuse existing engine), FAQ/help, toasts + confirmation modals (shared JS).

**3. Front Office** — room search + availability calendar, booking wizard (dates → room → extras → review → pay → e-ticket QR), walk-in registration, check-in (self OTP / desk), check-out + bill settlement, room status board (available/occupied/cleaning/maintenance/blocked), guest history, night audit (EOD close, occupancy rollover, revenue summary).

**4. Dining & Room Service** — foods/drinks/snacks menus (veg/non-veg, images, availability), cart with member 5% + GST, order lifecycle received→preparing→ready→served→paid, kitchen display queue with prep-time tracking, restaurant table layout (waiter), room mini bar orders, per-order QR pay.

**5. Housekeeping & Guest Services** — service request form (cleaning/laundry/ironing/maintenance, priority low/medium/high/urgent), role-based task boards sorted by priority then age, status flow pending→assigned→in_progress→completed with live updates to guest/manager/admin (3s polling), housekeeping room status sync, deep-cleaning schedule, lost & found register, linen tracker.

**6. Engineering / Maintenance** — work orders from guest reports/manager, preventive maintenance calendar (AC/plumbing/elevators/generator), asset register (warranty, service history), maintenance order detail.

**7. Concierge** — wake-up calls, taxi booking, airport transfers, tours & activities, doctor on call, local recommendations — requests flow to concierge queue, guest notified on completion.

**8. Accounts & Payments** — transaction ledger for all payments (rooms/dining/services/events/spa), invoice generation + print, QR payment verification console, refund processing with reason trail, daily settlement / POS close, GST/tax configuration.

**9. Events, Banquets & Wellness** — banquet/hall booking with capacity + catering packages, events calendar, spa/pool/gym slot reservations, event enquiry inbox.

**10. Manager / Operations** — occupancy %, revenue today/month, task load by department, pending QR payments; staff task assignment console; rooms & rate management; availability calendar; operations reports + CSV export; announcements broadcast by role; staff shifts & attendance; expense approvals.

**11. Admin / Platform** — full analytics (Chart.js: revenue by category/method/timeline, occupancy trend), user & role management, staff management, menu management (foods/drinks/snacks CRUD), service catalogue & pricing, promo codes & offers, audit logs, system settings, backup & data export (JSON/CSV).

**12. Security, Parking & Safety** — visitor log (entry/exit, host room, purpose), incident report register, parking slot management, emergency & safety board (evacuation routes, contact numbers).

**13. CRM, Loyalty & Marketing** — loyalty points on every ₹ spent, redeem at checkout; membership management (level, discount %, points); guest reviews & feedback with moderation; newsletter + campaigns (reuse existing admin).

---

## 6. Firestore Data Model

**Users**: `users`, `otp_codes`, `memberships`
**Rooms**: `rooms`, `room_types`, `rate_plans`, `bookings`
**Dining**: `foods`, `drinks`, `snacks`, `orders`, `restaurant_tables`, `mini_bar_orders`
**Services**: `service_requests`, `tasks`, `laundry_orders`, `lost_found`, `linen`
**Engineering**: `maintenance_orders`, `assets`
**Concierge**: `concierge_requests`
**Payments**: `transactions`, `invoices`, `qr_payments`, `refunds`
**Inventory**: `inventory`, `suppliers`, `purchase_orders`
**Events/Wellness**: `banquet_bookings`, `catering_packages`, `spa_bookings`, `pool_bookings`, `gym_bookings`
**Security**: `visitor_logs`, `incident_reports`, `parking_records`
**CRM**: `reviews`, `promo_codes`, `newsletter_subscribers`, `campaign_sends`, `loyalty_points_log`
**System**: `notifications`, `announcements`, `audit_logs`, `settings`, `night_audits`

Key shapes:

```json
// users
{ "email", "password_hash", "name", "phone", "role", "staff_role",
  "is_active", "discount_percent", "loyalty_points", "google_auth", "created_at" }

// otp_codes
{ "email", "code_hash", "expires_at", "purpose": "register|reset|checkin", "attempts", "created_at" }

// rooms
{ "number", "type", "price", "status": "available|occupied|cleaning|maintenance|blocked",
  "amenities", "max_guests", "floor", "image" }

// bookings
{ "booking_no", "user_email", "guest_name", "room_id", "room_number",
  "check_in", "check_out", "guests", "base_price", "discount_percent", "discount_amount",
  "tax", "total_price", "status": "confirmed|checked_in|checked_out|completed|cancelled",
  "source": "web|walkin|desk", "transaction_id", "e_ticket_qr", "created_at" }

// orders
{ "order_no", "user_email", "room_number",
  "items": [ { "item_id", "name", "qty", "price", "total" } ],
  "subtotal", "discount_percent", "discount_amount", "tax", "total",
  "status": "received|preparing|ready|served|paid",
  "payment_method": "qr|card|wallet|room_charge",
  "qr_code_url", "prep_start", "ready_at", "paid_at", "created_at" }

// service_requests
{ "request_no", "user_email", "room_number",
  "service_type": "cleaning|laundry|ironing|maintenance",
  "priority": "low|medium|high|urgent", "description",
  "status": "pending|assigned|in_progress|completed",
  "assigned_staff", "completed_at", "created_at" }

// tasks (derived from requests — what staff see)
{ "task_no", "source": "service|maintenance|housekeeping", "source_id",
  "room_number", "type", "priority", "description",
  "role": "housekeeping|laundry|maintenance|concierge",
  "status", "assigned_to", "started_at", "completed_at", "created_at" }

// qr_payments
{ "order_id", "order_no", "amount", "status": "pending|paid",
  "qr_code_url", "paid_by", "verified_by", "created_at" }

// transactions
{ "transaction_id", "user_email", "amount", "payment_method",
  "payment_status": "completed|refunded|pending",
  "category": "room|dining|service|event|spa",
  "reference_no", "billing_info", "created_at" }

// invoices
{ "invoice_no", "booking_id", "user_email", "items",
  "subtotal", "tax", "total", "status": "issued|paid|overdue|refunded",
  "qr_url", "created_at" }

// notifications
{ "target_role", "target_email", "title", "message", "is_read", "created_at" }

// settings
{ "key", "value" }   // hotel name, tax %, feature flags, default rates
```

**Read paths**: staff tasks → `tasks` where `status != completed` ordered by priority then age; room availability → `rooms` + `bookings` date-overlap; kitchen → `orders` where `status in (received, preparing)`.

---

## 7. Project Structure

```
Hotel Management System firebase/
├── app.py                       # Entry point — create_app()
├── master_plan.md
├── requirements.txt             # + qrcode, Pillow
├── config.py
├── app/
│   ├── __init__.py              # create_app(), blueprint registration, error handlers
│   ├── firebase_db.py           # Firestore client + collection helpers
│   ├── auth/                    # login, register, OTP, google, decorators
│   ├── core/                    # dashboard router, profile, notifications, search
│   ├── frontdesk/               # rooms, booking wizard, check-in/out, room board, night audit
│   ├── dining/                  # menus, cart, orders, kitchen queue, inventory, tables
│   ├── services/                # service requests, task queues, lost & found, linen
│   ├── concierge/               # concierge requests
│   ├── payments/                # process payment, QR, invoices, refunds, settlement
│   ├── events/                  # banquets, catering, spa/pool/gym
│   ├── security/                # visitor log, incidents, parking
│   ├── manager/                 # manager dashboard, assignment, reports, announcements
│   └── admin/                   # analytics, users, menu CRUD, audit, settings, backup
├── static/
│   ├── css/theme.css            # Google × Apple design system
│   ├── js/main.js               # shared JS: api(), toasts, modals, polling
│   └── images/
└── templates/
    ├── auth/  components/  dashboard/
    ├── guest/  frontdesk/  dining/  services/  concierge/
    ├── payments/  events/  security/
    ├── manager/  admin/
```

---

## 8. Screen Inventory — 90 Screens

### Module 1 — Auth & Onboarding (6)
| ID | Screen | Roles |
|---|---|---|
| SCR-01 | Login | All |
| SCR-02 | Register (name/email/phone/password + role select) | Public |
| SCR-03 | OTP Verify (register/reset/checkin) | Public |
| SCR-04 | Forgot Password | Public |
| SCR-05 | Reset Password | Public |
| SCR-06 | Google SSO / account link | All |

### Module 2 — Common (5)
| ID | Screen | Roles |
|---|---|---|
| SCR-07 | Profile & Settings | All |
| SCR-08 | Notifications Center | All |
| SCR-09 | Global Search | Staff+ |
| SCR-10 | AI Assistant / Chatbot | All |
| SCR-11 | FAQ / Help Center | All |

### Module 3 — Front Office & Guest (12)
| ID | Screen | Roles |
|---|---|---|
| SCR-12 | Guest Dashboard | user/member |
| SCR-13 | Room Search & Availability | user/member/desk |
| SCR-14 | Room Booking Wizard | user/member/desk |
| SCR-15 | Payment Checkout | user/member |
| SCR-16 | My Bookings | user/member |
| SCR-17 | Booking e-Ticket with QR | user/member |
| SCR-18 | Check-in (self OTP / front desk) | user/member/desk |
| SCR-19 | Check-out & Bill Settlement | user/member/desk |
| SCR-20 | Room Status Board | front_desk/manager/admin |
| SCR-21 | Walk-in Registration | front_desk |
| SCR-22 | Guest History & Profiles | front_desk |
| SCR-23 | Night Audit | front_desk/manager |

### Module 4 — Dining & Room Service (10)
| ID | Screen | Roles |
|---|---|---|
| SCR-24 | Dining Menu — Foods | user/member |
| SCR-25 | Drinks Menu | user/member |
| SCR-26 | Snacks Menu | user/member |
| SCR-27 | Cart & Checkout (member 5% + GST) | user/member |
| SCR-28 | My Orders / Live Status Trail | user/member |
| SCR-29 | Order QR Pay | user/member |
| SCR-30 | Kitchen Display Queue | chef |
| SCR-31 | Restaurant Table Layout | waiter/cashier |
| SCR-32 | Mini Bar | user/member/desk |
| SCR-33 | Kitchen Inventory & Low-Stock | chef/admin |

### Module 5 — Housekeeping & Guest Services (10)
| ID | Screen | Roles |
|---|---|---|
| SCR-34 | Housekeeping Task Board | housekeeping |
| SCR-35 | Service Request Form | user/member |
| SCR-36 | My Service Requests (live status) | user/member |
| SCR-37 | Laundry Task Board | laundry |
| SCR-38 | Maintenance Work Orders | maintenance |
| SCR-39 | Lost & Found Register | housekeeping/manager |
| SCR-40 | Linen Tracker | housekeeping |
| SCR-41 | Task Detail (in-progress → completed) | staff |
| SCR-42 | Housekeeping Room Status | housekeeping/desk |
| SCR-43 | Deep Cleaning Schedule | housekeeping/manager |

### Module 6 — Engineering / Maintenance (4)
| ID | Screen | Roles |
|---|---|---|
| SCR-44 | Work Order Queue | maintenance |
| SCR-45 | Preventive Maintenance Calendar | maintenance/manager |
| SCR-46 | Asset Register | maintenance/admin |
| SCR-47 | Maintenance Order Detail | maintenance/manager |

### Module 7 — Concierge (5)
| ID | Screen | Roles |
|---|---|---|
| SCR-48 | Concierge Request (wake-up/taxi/tour/doctor) | user/member |
| SCR-49 | Airport Transfers Board | concierge |
| SCR-50 | Tours & Activities Booking | user/member/concierge |
| SCR-51 | Doctor on Call | concierge/desk |
| SCR-52 | Local Guide Recommendations | user/member |

### Module 8 — Accounts & Payments (6)
| ID | Screen | Roles |
|---|---|---|
| SCR-53 | Transaction Ledger | accountant/manager/admin |
| SCR-54 | Invoice Management + Print | accountant/admin |
| SCR-55 | QR Payment Verification Console | manager/admin |
| SCR-56 | Refund Processing | accountant/admin |
| SCR-57 | Daily Settlement / POS Close | accountant |
| SCR-58 | Tax & Rate Configuration | admin |

### Module 9 — Events, Banquets & Wellness (6)
| ID | Screen | Roles |
|---|---|---|
| SCR-59 | Banquet / Hall Booking | user/member/events |
| SCR-60 | Catering Packages | events/manager |
| SCR-61 | Events Calendar | manager/admin |
| SCR-62 | Spa & Wellness Booking | user/member |
| SCR-63 | Pool & Gym Reservations | user/member |
| SCR-64 | Event Enquiry Inbox | front_desk/manager |

### Module 10 — Manager / Operations (8)
| ID | Screen | Roles |
|---|---|---|
| SCR-65 | Manager Dashboard | manager/admin |
| SCR-66 | Staff Task Assignment Console | manager/admin |
| SCR-67 | Rooms & Rate Management | manager/admin |
| SCR-68 | Availability Calendar | manager/admin |
| SCR-69 | Operations Reports + CSV Export | manager/admin |
| SCR-70 | Announcements / Broadcasts | manager/admin |
| SCR-71 | Staff Shifts & Attendance | manager/admin |
| SCR-72 | Expense Approvals | manager/admin |

### Module 11 — Admin / Platform (10)
| ID | Screen | Roles |
|---|---|---|
| SCR-73 | Admin Dashboard (full analytics) | admin |
| SCR-74 | Transaction Analytics (Chart.js) | admin |
| SCR-75 | User & Role Management | admin |
| SCR-76 | Staff Management (roles/shifts) | admin |
| SCR-77 | Menu Management (foods/drinks/snacks CRUD) | admin |
| SCR-78 | Service Catalogue & Pricing | admin |
| SCR-79 | Promo Codes & Offers | admin |
| SCR-80 | Audit Logs | admin |
| SCR-81 | System Settings | admin |
| SCR-82 | Backup & Data Export | admin |

### Module 12 — Security, Parking & Safety (4)
| ID | Screen | Roles |
|---|---|---|
| SCR-83 | Visitor Log | front_desk/security |
| SCR-84 | Incident Report Register | security/manager |
| SCR-85 | Parking Management | security/front_desk |
| SCR-86 | Emergency & Safety Board | all |

### Module 13 — CRM, Loyalty & Marketing (4)
| ID | Screen | Roles |
|---|---|---|
| SCR-87 | Loyalty Points & Rewards | user/member |
| SCR-88 | Membership Management | admin |
| SCR-89 | Reviews & Feedback (moderation) | user/member/admin |
| SCR-90 | Newsletter & Campaigns (reuse existing) | admin |

**Total: 90 screens.** Each role's dashboard aggregates its module screens with quick actions.

---

## 9. API Endpoints

**Auth**: `POST /api/auth/register`, `/verify-otp`, `/resend-otp`, `/login`, `/google`, `/logout`, `/forgot`, `/reset`

**Rooms & Bookings**: `GET /api/rooms/available?check_in&check_out&type`, `GET/POST/PUT /api/rooms[/id]`, `GET /api/bookings`, `POST /api/bookings`, `POST /api/bookings/<id>/cancel|checkin|checkout`, `GET /api/frontdesk/room-board`, `POST /api/frontdesk/walkin`

**Dining**: `GET /api/menu?category=food|drink|snack`, `POST /api/orders`, `GET /api/orders`, `POST /api/orders/<id>/status|pay`, `GET /api/kitchen/queue`, `POST /api/restaurant/tables/<id>/state`, `POST /api/minibar/order`

**Services**: `POST /api/service-requests`, `GET /api/service-requests`, `POST /api/tasks/<id>/assign|status`, `GET /api/laundry/orders`, `POST /api/laundry/<id>/status`, `GET/POST /api/lost-found`

**Concierge**: `POST /api/concierge/requests`, `GET /api/concierge/requests`, `POST /api/concierge/<id>/status`

**Payments**: `POST /api/payments/process` (simulated card/UPI/wallet/netbanking), `GET /api/transactions`, `GET /api/invoices/<id>`, `POST /api/qr-payments/<id>/verify`, `POST /api/refunds`, `POST /api/accounts/settlement`, `GET /api/accounts/ledger`

**Manager/Admin**: `GET /api/analytics/overview|transactions|occupancy`, `GET /api/admin/users`, `POST /api/admin/users/<id>/role|toggle`, `POST /api/admin/menu`, `POST /api/admin/services-catalogue`, `POST /api/admin/promo-codes`, `GET /api/admin/audit-logs`, `GET/PUT /api/admin/settings`, `GET /api/admin/export?collection=users|bookings|transactions`, `POST /api/manager/reports`, `POST /api/announcements`, `GET /api/reviews`, `POST /api/reviews/<id>/moderate`

---

## 10. Design System (Google × Apple)

```css
:root {
  --google-blue: #4285F4;   --google-red: #EA4335;
  --google-yellow: #FBBC05; --google-green: #34A853;
  --apple-bg: #F5F5F7;      --card-bg: #FFFFFF;
  --text-primary: #1D1D1F;  --text-secondary: #6E6E73;
  --border: #E5E5EA;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.08);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08);
  --radius-lg: 16px;  --radius-xl: 22px;
  --font: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
}
```

- Light theme, white cards on `#F5F5F7`, hairline borders, soft shadows.
- Pill buttons, 44px+ touch targets.
- **Priority pills**: urgent=red, high=orange, medium=blue, low=gray.
- **Status pills**: received=gray, preparing=blue, ready=yellow, served=green, paid=green, completed=green, cancelled=red.
- Role dashboards: sidebar nav for staff/manager/admin; tab quick-nav for guests on mobile.

---

## 11. Implementation Phases

**Phase 1 — Foundation**: `config.py`, `app/firebase_db.py`, `create_app()` factory, blueprint registration, `login_required` + `role_required(...)` decorators, `theme.css` + `main.js` (toasts, modals, `api()`, polling), shared template components.

**Phase 2 — Auth & Roles**: register with role selection → OTP → verify → login; OTP service (generate, bcrypt-hash, store, 5-min expiry, 5 attempts); role-routed `/dashboard`; seed accounts for all 12 roles; profile, notifications center.

**Phase 3 — Front Office & Guest**: room search + availability + booking wizard + e-ticket QR; payment checkout (simulated) + promo codes; check-in (OTP self / desk) + check-out + bill settlement; room status board, walk-in, guest history, night audit.

**Phase 4 — Dining & Room Service**: menu CRUD + 3 menu pages + cart with member 5% + GST; order creation + QR generation + pay; kitchen display queue + order status updates + inventory alerts; restaurant table layout + mini bar.

**Phase 5 — Services / Maintenance / Laundry / Concierge**: service request form + priority + live status for guest; task boards per staff role (priority-sorted) + task detail + assign/complete; lost & found, linen tracker, work orders, assets; concierge request queue.

**Phase 6 — Manager & Operations**: manager dashboard (occupancy, revenue, task load); task assignment console; rooms & rate management; availability calendar; operations reports + CSV; announcements; shifts; expenses.

**Phase 7 — Admin Platform**: admin dashboard + transaction analytics (Chart.js); user & role management; staff management; menu / service catalogue / promo codes management; audit logs; system settings; backup & export; review moderation.

**Phase 8 — QA, Security & Deployment**: smoke-test every endpoint with curl (role-gated); responsive pass (≥375px), fix overflow/clipping; update `requirements.txt` (qrcode, Pillow), `.env.example`, `DEPLOYMENT_GUIDE.md`; security pass (OTP rate limit, password policy, role checks on every route); git commit.

---

## 12. Documented Hooks (later integration)

| Hook | Where | Later |
|---|---|---|
| Real email/SMS OTP | `app/auth/otp_service.py` | SendGrid/Twilio |
| Real payment gateway | `app/payments/routes.py` | Razorpay/Stripe |
| Realtime push | core polling helper (3–5s) | Firebase Cloud Messaging |
| Multi-hotel | `settings` `hotel_id` scoping | add `hotel_id` to collections |
| POS / receipt printers | `payments` settlement | printer integration |

---

## 13. Definition of Done

- All 13 modules have routes, templates, and data collections
- All 90 screens (Section 8) reachable from a role dashboard
- Staff task completion propagates live to guest/manager/admin views
- Member 5% discount applied consistently across booking, dining, services
- OTP registration flow works end-to-end (backend)
- QR generation + verification flow works
- Google × Apple design system applied across all screens
- Every endpoint smoke-tested; responsive pass done; docs updated
