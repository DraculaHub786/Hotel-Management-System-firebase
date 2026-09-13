# Hotel Management SaaS — Detailed Spec (Screens, Forms, API Contracts, UI States)

This extends the architecture/build-order plan with the level of detail needed to actually build against: every screen per role, field-level form specs, JSON API contracts, and the UI states each screen must handle. Wireframes are described as text layouts (regions + content), not images — translate directly into your component shell.

---

<!--
## A. Shared Conventions (apply everywhere, referenced instead of repeated) - COMPLETED

### A.1 Standard UI states — every list/table/detail screen must implement all five
1. **Loading** — skeleton rows/cards matching the real layout (not a spinner-only screen) for anything expected to take >300ms.
2. **Empty** — icon + one-line message + a primary action if one exists (e.g. "No tasks assigned yet" / "No bookings for this date").
3. **Error** — message + "Retry" button; never a blank white screen or raw error text.
4. **Success (transient)** — toast, 3–4s auto-dismiss, top-right; used after create/update/delete actions.
5. **Permission-denied** — shown when a role-gated screen is hit directly by URL without permission: short message + "Return to dashboard" link, logged to `audit_logs` as a denied-access attempt.

### A.2 Standard list/table screen shape
Every "queue" or "board" screen (tasks, orders, tickets, bookings) shares this layout region set unless noted otherwise:
```
[Topbar: title | search input | filter chips | + New button (if applicable)]
[Filter bar: status tabs/pills, date range, assignee dropdown — only fields relevant to that entity]
[Content: table (desktop) / stacked cards (tablet-friendly, ≤1024px)]
[Pagination or infinite scroll footer]
```

### A.3 Standard form conventions
- Required fields marked with `*`, validated on blur (not only on submit).
- Submit button disabled until required fields are valid; shows inline spinner while submitting, then either closes/redirects or shows field-level error(s) returned from the API.
- Every form has a `Cancel`/`Back` action that discards changes with a confirm dialog only if the form is dirty.
- Server-side validation errors map to specific fields by key name (see API contracts — error responses always return `{ "errors": { "field_name": "message" } }`).

### A.4 Standard API envelope
```json
// Success
{ "ok": true, "data": { ... } }

// Error
{ "ok": false, "errors": { "field_name": "Human readable message" }, "message": "Optional top-level message" }
```
All endpoints below follow this envelope; only the `data` shape is documented per-endpoint from here on.

### A.5 Standard permission-denied API response
```json
// HTTP 403
{ "ok": false, "message": "You do not have permission to perform this action." }
```
-->


---

<!--
## B. Auth Screens (shared by all roles) - COMPLETED

### B.1 Screen inventory
| Screen | Route | Roles |
|---|---|---|
| Login | `/login` | all |
| Guest Signup | `/signup` | guest only (staff have no public signup) |
| Staff Invite Accept (set password) | `/invite/<token>` | invited staff only, token-gated |
| Forgot Password | `/forgot-password` | all |
| Reset Password | `/reset-password/<token>` | all |

### B.2 Login form — field-level spec
| Field | Type | Validation | Notes |
|---|---|---|---|
| `email` | text | required, valid email format | autofocus |
| `password` | password | required, min 8 chars | show/hide toggle icon |
| — | checkbox | "Remember me" (optional, extends session cookie lifetime) | |

States: default → submitting (button spinner) → error (`Invalid email or password` — never say which field is wrong) → 5 failed attempts in 10 min triggers a rate-limit error (`Too many attempts, try again in N minutes`) per Section 10 rate-limiting.

**Layout:**
```
[Centered card, 400px wide]
  [Logo]
  [Heading: "Sign in"]
  [Email input]
  [Password input]
  [Remember me checkbox]  [Forgot password? link]
  [Sign in button — full width]
  [Divider "or"]
  [Continue with Google button]
  [Don't have an account? Sign up — hidden if role param indicates staff-only context]
```

### B.3 API — `POST /api/auth/login`
Request:
```json
{ "email": "guest@example.com", "password": "••••••••" }
```
Response `data`:
```json
{
  "user": { "uid": "abc123", "name": "Jane Doe", "role": "guest", "property_id": "prop_1" },
  "redirect": "/dashboard"
}
```
Sets an httpOnly session cookie; role and property_id are never accepted from the client on this call — derived server-side from the stored user doc.

### B.4 Staff Invite Accept — field-level spec
| Field | Type | Validation |
|---|---|---|
| `name` (pre-filled, editable) | text | required |
| `password` | password | required, min 10 chars, 1 number, 1 symbol (staff accounts held to a stricter policy than guests) |
| `confirm_password` | password | must match `password` |

Invalid/expired token state: full-page message "This invite link has expired — ask your admin to resend it," no form shown.

### B.5 API — `POST /api/auth/invite/accept`
Request:
```json
{ "token": "inv_9f2...", "name": "Ravi Kumar", "password": "••••••••••" }
```
Response `data`:
```json
{ "user": { "uid": "xyz789", "role": "housekeeping", "department_id": "dept_hsk" }, "redirect": "/staff/housekeeping" }
```
Server validates: token exists in an `invites` collection (not yet modeled above — add `invites/{invite_id}: { email, role, department_id, property_id, invited_by, expires_at, used: bool }`), not expired, not already used, marks `used: true` on success.
-->


---

<!--
## C. Guest Screens - COMPLETED

### C.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Home / Dashboard | `/dashboard` |
| 2 | Rooms Browse | `/rooms` |
| 3 | Room Detail | `/rooms/<room_id>` |
| 4 | Facilities Browse | `/facilities` |
| 5 | Facility Detail + Slot Picker | `/facilities/<facility_id>` |
| 6 | Menu Browse | `/menu` |
| 7 | Cart | `/cart` |
| 8 | Checkout | `/checkout` |
| 9 | Payment — QR Display | `/pay/<txn_id>` |
| 10 | Payment — OTP Entry | `/pay/<txn_id>/otp` |
| 11 | Booking Confirmation | `/confirmation/<booking_id>` |
| 12 | My Bookings / Orders (history) | `/my-bookings` |
| 13 | Booking Detail (cancel action here) | `/my-bookings/<id>` |
| 14 | Support / Chat | `/support` |
| 15 | Profile / Account Settings | `/account` |

### C.2 Room Detail — layout
```
[Image gallery — main image + thumbnail strip, left 60%]
[Right 40%: Room name, price/night, capacity, amenities list (icons+labels),
 date-range picker, guest count stepper, "Add to cart" button (disabled until dates chosen)]
[Below fold: description, policies (cancellation, check-in/out times), reviews (if in scope)]
```
States: Loading → skeleton gallery + text bars. Room unavailable for chosen dates → date picker shows disabled dates in red, "Add to cart" stays disabled with helper text "Not available for these dates."

### C.3 Cart — field-level spec
Cart is a single object holding 3 line-item types. Each line item row shows: thumbnail, name, date/qty selector (editable inline), unit price, line total, remove (×) icon.
```
CartItem:
  - type: "room" | "facility" | "menu"
  - ref_id
  - qty (menu only; rooms/facilities are qty=1 per date range/slot)
  - date_range or slot (room/facility)
  - unit_price
```
Empty state: "Your cart is empty" + "Browse rooms" button.

### C.4 Checkout — field-level spec
| Field | Type | Validation |
|---|---|---|
| Guest name | text (pre-filled from profile) | required |
| Phone | tel | required, valid format |
| Special requests | textarea | optional, max 500 chars |
| Delivery vs Dine-in (menu items only) | radio | required if cart has menu items |
| — | line-item summary (read-only) | subtotal, tax %, service charge %, total |
| Terms checkbox | checkbox | required to enable Pay button |

### C.5 API — `POST /api/cart/checkout`
Request:
```json
{
  "items": [
    { "type": "room", "ref_id": "room_204", "check_in": "2026-09-20", "check_out": "2026-09-22" },
    { "type": "menu", "ref_id": "item_12", "qty": 2 }
  ],
  "delivery_mode": "in_room",
  "special_requests": "Late check-in around 11pm"
}
```
Response `data`:
```json
{
  "order_summary": {
    "subtotal": 8200.00,
    "tax": 410.00,
    "service_charge": 205.00,
    "total": 8815.00,
    "currency": "INR"
  },
  "txn_id": "txn_88f2a1"
}
```
Server recalculates all prices from the DB (never trusts client-sent prices), applies `pricing_rules` config, creates a `transactions` doc with `status: "pending"`.

### C.6 Payment QR screen — layout
```
[Centered card]
  [Total amount, large]
  [QR code image — base64 PNG from server]
  [Instruction: "Scan with your phone to confirm payment"]
  [Countdown timer — QR expires in 10 min, then auto-refreshes payload]
  [Small text link: "Trouble scanning? Use this link instead" → same confirm URL]
[Below: live status poll/listener — "Waiting for payment confirmation..." spinner, auto-navigates to OTP screen the instant `transactions.status` flips to "paid"]
```

### C.7 API — `POST /api/payment/create-qr`
Request:
```json
{ "txn_id": "txn_88f2a1" }
```
Response `data`:
```json
{
  "qr_image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "qr_payload": "https://yourapp.com/pay/confirm/txn_88f2a1",
  "expires_at": "2026-09-08T14:32:00Z"
}
```

### C.8 API — `POST /api/otp/verify`
Request:
```json
{ "txn_id": "txn_88f2a1", "otp": "482913" }
```
Response `data` (success):
```json
{
  "booking_id": "bk_5521",
  "confirmation_code": "HTL-5521-AX",
  "receipt_url": "/api/receipt/txn_88f2a1"
}
```
Response (wrong OTP, attempt 2 of 5):
```json
{ "ok": false, "errors": { "otp": "Incorrect code. 3 attempts remaining." } }
```
Response (locked out):
```json
{ "ok": false, "message": "Too many incorrect attempts. Request a new code." }
```

### C.9 My Bookings — list screen
Columns/cards: booking ref, room/facility name, dates, status badge (`confirmed`/`checked_in`/`checked_out`/`cancelled`), total paid, action menu (View, Cancel — cancel only visible if `status: confirmed` and check-in is >24h away, per cancellation policy).
-->

---

<!--
## D. Front Desk Screens - COMPLETED

### D.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Today's Arrivals/Departures | `/staff/front-desk` |
| 2 | Room Status Board | `/staff/front-desk/rooms` |
| 3 | Booking Detail / Check-in action | `/staff/front-desk/bookings/<id>` |
| 4 | Check-out action | (modal from Room Status Board) |

### D.2 Room Status Board — layout
Grid of room cards, one per room, color-coded: green=available, blue=occupied, yellow=dirty/needs cleaning, orange=cleaning in progress, red=maintenance block.
```
[Filter bar: floor selector, status filter chips]
[Grid: room number, status color, guest name if occupied, quick-action button
 (Check-in / Check-out / Mark Clean — button changes based on status)]
```
Clicking a card opens a side-drawer with full room + current booking detail rather than navigating away (keeps the board in context).

### D.3 Check-in form — field-level spec
| Field | Type | Validation |
|---|---|---|
| Booking reference (search/select) | typeahead | required |
| ID verification confirmed | checkbox | required to enable Confirm |
| Room assignment (if not pre-assigned) | dropdown of available rooms | required |
| Notes | textarea | optional |

### D.4 API — `POST /api/front-desk/checkin`
Request:
```json
{ "booking_id": "bk_5521", "room_id": "room_204", "id_verified": true, "notes": "" }
```
Response `data`:
```json
{ "booking_id": "bk_5521", "status": "checked_in", "checked_in_at": "2026-09-08T13:05:00Z" }
```

### D.5 API — `POST /api/front-desk/checkout`
Request:
```json
{ "booking_id": "bk_5521" }
```
Response `data`:
```json
{
  "booking_id": "bk_5521",
  "status": "checked_out",
  "checked_out_at": "2026-09-08T15:40:00Z",
  "housekeeping_task_id": "task_9911"
}
```
Server-side side effect (not client-triggered): auto-creates a `housekeeping_tasks` doc with `type: "checkout_clean"`, `status: "pending"`, `room_id`, `created_from: "booking_checkout"` — this is the automation link called out in the original plan.
-->


---

<!--
## E. Housekeeping Screens - COMPLETED

### E.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Task Board (Kanban) | `/staff/housekeeping` |
| 2 | Task Detail | `/staff/housekeeping/tasks/<id>` |
| 3 | Report Issue modal | (opened from Task Detail) |

### E.2 Task Board — layout
```
[Columns: Pending | In Progress | Done]
[Each card: room number, task type badge, priority flag (VIP/guest-waiting/standard), assigned-to avatar]
[Drag-and-drop between columns OR tap card → status dropdown (tablet-friendly fallback, since drag-drop is unreliable on touch)]
```

### E.3 Report Issue modal — field-level spec
| Field | Type | Validation |
|---|---|---|
| Issue type | dropdown (Plumbing, Electrical, AC/Heating, Furniture, Other) | required |
| Description | textarea | required, max 500 chars |
| Photo | file upload, image only | optional, max 5MB |
| Priority | radio (Low/Medium/High) | required |

### E.4 API — `PATCH /api/housekeeping/tasks/<id>`
Request:
```json
{ "status": "in_progress" }
```
Response `data`:
```json
{ "task_id": "task_9911", "status": "in_progress", "updated_at": "2026-09-08T13:10:00Z" }
```

### E.5 API — `POST /api/housekeeping/tasks/<id>/report-issue`
Request:
```json
{ "issue_type": "ac_heating", "description": "AC unit leaking water near window", "priority": "high" }
```
Response `data`:
```json
{ "maintenance_ticket_id": "tkt_4432", "room_id": "room_204" }
```
-->

---

<!--
## F. Laundry Screens - COMPLETED

### F.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Task Board (Kanban: Collected → Washing → Ready → Delivered) | `/staff/laundry` |
| 2 | Task Detail | `/staff/laundry/tasks/<id>` |

### F.2 Task Detail — field-level spec (create/edit)
| Field | Type | Validation |
|---|---|---|
| Room/Guest | typeahead | required |
| Items (repeatable: name, qty) | dynamic list | at least 1 item required |
| Pickup time | datetime | required |
| Delivery time (est.) | datetime | optional until status=ready |

### F.3 API — `PATCH /api/laundry/tasks/<id>`
Request:
```json
{ "status": "ready", "delivery_time": "2026-09-08T18:00:00Z" }
```
Response `data`:
```json
{ "task_id": "lt_221", "status": "ready" }
```
-->

---

<!--
## G. Room Service Screens - COMPLETED

### G.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Incoming Orders Queue | `/staff/room-service` |
| 2 | Order Detail | `/staff/room-service/orders/<id>` |

### G.2 Order Detail — layout
```
[Order items list with qty]
[Room number, delivery notes]
[Status stepper: Received → Preparing → Ready → Delivering → Delivered]
[If order value > threshold: "Require OTP at delivery" toggle (admin-configured default)]
```

### G.3 API — `PATCH /api/orders/<id>/status`
Request:
```json
{ "status": "delivering" }
```
Response `data`:
```json
{ "order_id": "ord_771", "status": "delivering" }
```
If OTP required and status transitions to `delivered`, request must include `otp`:
```json
{ "status": "delivered", "otp": "119284" }
```
-->

---

<!--
## H. Kitchen Screens - COMPLETED

### H.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Combined Orders Queue (room service + restaurant) | `/staff/kitchen` |
| 2 | Menu Availability Toggle list | `/staff/kitchen/menu` |

### H.2 Menu Availability — layout
Simple table: item name, category, price, `Available` toggle switch (instant save on toggle, optimistic UI with rollback on error).

### H.3 API — `PATCH /api/menu-items/<id>/availability`
Request:
```json
{ "available": false }
```
Response `data`:
```json
{ "item_id": "item_12", "available": false }
```
This write is shared/visible identically on the guest `/menu` page (same source doc) and on Admin's menu management screen.
-->

---

<!--
## I. Security Screens - COMPLETED

### I.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Incident Log List | `/staff/security` |
| 2 | New Incident form | `/staff/security/new` |
| 3 | Incident Detail | `/staff/security/<id>` |
| 4 | Check-in Verification Flags | `/staff/security/flags` |

### I.2 New Incident — field-level spec
| Field | Type | Validation |
|---|---|---|
| Type | dropdown (Disturbance, Theft, Unauthorized access, Medical, Other) | required |
| Location | text or room typeahead | required |
| Description | textarea | required, max 1000 chars |
| Severity | radio (Low/Medium/High/Critical) | required |
| Photo/evidence | file upload | optional |

`Critical` severity auto-fires a high-priority notification to Admin (per Section 5.7 panic-button behavior).

### I.3 API — `POST /api/security/incidents`
Request:
```json
{ "type": "disturbance", "location_room_id": "room_309", "description": "Loud argument reported by neighboring guest", "severity": "medium" }
```
Response `data`:
```json
{ "incident_id": "inc_331", "status": "open", "created_at": "2026-09-08T22:15:00Z" }
```
-->

---

<!--
## J. Maintenance Screens - COMPLETED

### J.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Ticket Queue | `/staff/maintenance` |
| 2 | Ticket Detail | `/staff/maintenance/tickets/<id>` |

### J.2 Ticket Detail — status flow
`Reported → Assigned → In Progress → Resolved`. Resolving requires a resolution note (required textarea) and auto-clears any maintenance block on the linked room's availability (server-side side effect).

### J.3 API — `PATCH /api/maintenance/tickets/<id>`
Request:
```json
{ "status": "resolved", "resolution_note": "Replaced AC compressor unit" }
```
Response `data`:
```json
{ "ticket_id": "tkt_4432", "status": "resolved", "room_unblocked": true }
```
-->

---

<!--
## K. Admin Screens - COMPLETED

### K.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Overview / Home | `/admin` |
| 2 | Staff List | `/admin/staff` |
| 3 | Invite Staff form | `/admin/staff/invite` |
| 4 | Staff Detail (deactivate/reassign) | `/admin/staff/<id>` |
| 5 | Rooms List | `/admin/rooms` |
| 6 | Room Create/Edit form | `/admin/rooms/<id>` or `/new` |
| 7 | Facilities List + Create/Edit | `/admin/facilities` |
| 8 | Menu List + Create/Edit | `/admin/menu` |
| 9 | Bookings & Orders Oversight | `/admin/bookings` |
| 10 | Revenue Dashboard | `/admin/revenue` |
| 11 | Incident/Maintenance Rollup | `/admin/incidents` |
| 12 | Refund Approval Queue | `/admin/refunds` |

### K.2 Invite Staff — field-level spec
| Field | Type | Validation |
|---|---|---|
| Name | text | required |
| Email | email | required, valid format, must not already exist as a user |
| Role | dropdown (all staff roles) | required |
| Department | dropdown (filtered by selected role) | required |
| Employee ID | text | optional, auto-generated if blank (`{DEPT}-{seq}`) |
| Shift start/end/days | time + multi-select days | optional at invite time, editable later |

### K.3 API — `POST /api/admin/staff/invite`
Request:
```json
{ "name": "Ravi Kumar", "email": "ravi@example.com", "role": "housekeeping", "department_id": "dept_hsk" }
```
Response `data`:
```json
{ "invite_id": "inv_9f2a", "email_sent": true, "expires_at": "2026-09-11T00:00:00Z" }
```
Server rejects (403) if `role` in payload is `admin` or `super_admin` and caller is not `super_admin` — admins cannot self-elevate or create other admins.

### K.4 Room Create/Edit — field-level spec
| Field | Type | Validation |
|---|---|---|
| Room number | text | required, unique per property |
| Type | dropdown (Single/Double/Suite/Deluxe...) | required |
| Price/night | number | required, > 0 |
| Capacity | number stepper | required, ≥ 1 |
| Amenities | multi-select chips | optional |
| Images | multi-file upload, drag-reorder | at least 1 required |
| Floor | number | required |
| Status | dropdown (available/maintenance) | required, default available |

### K.5 API — `POST /api/admin/rooms`
Request:
```json
{
  "number": "204",
  "type": "deluxe",
  "price_per_night": 4500,
  "capacity": 3,
  "amenities": ["wifi", "minibar", "balcony"],
  "floor": 2
}
```
Response `data`:
```json
{ "room_id": "room_204" }
```
(Image upload is a separate multipart endpoint `POST /api/admin/rooms/<id>/images` returning uploaded URLs.)

### K.6 Revenue Dashboard — layout
```
[Date range selector: Today / 7d / 30d / Custom]
[KPI row: Total Revenue, Occupancy Rate %, Avg Order Value, Bookings Count]
[Line chart: revenue over time]
[Bar chart: top 10 menu items by revenue]
[Table: revenue breakdown by category — rooms / facilities / menu]
```

### K.7 API — `GET /api/admin/revenue?range=30d`
Response `data`:
```json
{
  "total_revenue": 812400.00,
  "occupancy_rate": 0.78,
  "avg_order_value": 3120.50,
  "bookings_count": 143,
  "revenue_over_time": [{ "date": "2026-08-10", "amount": 24500 }, "..."],
  "top_menu_items": [{ "item_id": "item_12", "name": "Club Sandwich", "revenue": 18400 }]
}
```

### K.8 Refund Approval — field-level spec
List screen: guest name, booking ref, requested amount, reason, requested date, Approve/Reject buttons. Approve opens a confirm dialog (irreversible, logged to `audit_logs` with before/after).

### K.9 API — `POST /api/admin/refunds/<id>/approve`
Response `data`:
```json
{ "refund_id": "rf_88", "status": "approved", "transaction_status": "refunded" }
```
-->

---

<!--
## L. Super Admin Screens - COMPLETED

### L.1 Screen inventory
| # | Screen | Route |
|---|---|---|
| 1 | Admin Management | `/super-admin/admins` |
| 2 | Create Admin form | `/super-admin/admins/new` |
| 3 | Property Management | `/super-admin/properties` |
| 4 | Property Create/Edit form | `/super-admin/properties/<id>` |
| 5 | Global Settings | `/super-admin/settings` |
| 6 | Audit Log Viewer | `/super-admin/audit-log` |
| 7 | Impersonation launcher (optional) | `/super-admin/impersonate` |

### L.2 Global Settings — field-level spec (tabbed sections)
- **Payment**: gateway provider dropdown, API key (masked input, write-only — never returned by GET), webhook secret.
- **OTP**: provider (Twilio/SendGrid), OTP length (default 6), expiry minutes (default 5), max attempts (default 5).
- **Pricing defaults**: tax %, service charge %.
- **Feature flags**: toggles, e.g. `facility_booking_enabled`, `dark_mode_enabled`.

### L.3 API — `GET /api/super-admin/settings`
Response `data` (secrets masked):
```json
{
  "payment": { "provider": "razorpay", "api_key": "rzp_live_••••1234" },
  "otp": { "provider": "twilio", "length": 6, "expiry_minutes": 5, "max_attempts": 5 },
  "pricing": { "tax_percent": 5, "service_charge_percent": 2.5 },
  "feature_flags": { "facility_booking_enabled": true, "dark_mode_enabled": false }
}
```

### L.4 Audit Log Viewer — layout
```
[Filter bar: actor dropdown, action-type dropdown, date range]
[Table: timestamp, actor name+role, action, target type/id, "View diff" link]
[View diff opens a modal with before/after JSON side-by-side]
```

### L.5 API — `GET /api/super-admin/audit-log?actor=...&action=...&from=...&to=...`
Response `data`:
```json
{
  "logs": [
    {
      "log_id": "log_5591",
      "actor_id": "uid_admin1",
      "actor_role": "admin",
      "action": "refund_approved",
      "target_type": "transaction",
      "target_id": "txn_88f2a1",
      "before": { "status": "pending_refund" },
      "after": { "status": "refunded" },
      "timestamp": "2026-09-08T16:02:00Z"
    }
  ],
  "next_cursor": "cursor_abc"
}
```
-->

---

<!--
## M. Cross-Cutting: Shared Shell Layout (all authenticated roles) - COMPLETED

```
[Sidebar — left, 240px, collapsible on tablet]
  [Logo]
  [Nav items — filtered server-side per role, never just hidden in CSS]
  [Bottom: user avatar + name + role badge, logout]

[Topbar — full width above content]
  [Search (context-aware: searches rooms/guests/tasks depending on role)]
  [Notification bell — badge count, dropdown of last 10 notifications]
  [Shift clock-in/out widget — staff roles only]

[Content area — role-specific screen renders here]
```

Responsive rule: at ≤1024px, sidebar collapses to icon-only; at ≤768px, sidebar becomes a bottom nav bar or hamburger drawer — test both explicitly per Section 8.

---

## N. What's Still Needed Before Build (per-screen, not yet done here)

This document brings every screen to a buildable level of detail for the *core* flows. Two things intentionally left out, to be done just-in-time per phase rather than all upfront (they'll drift if written 6 phases early):

- **Actual pixel-level wireframes/mockups** (Figma-equivalent) — once Section H (design tokens) is picked, I can generate visual mockups per screen using the design system, rather than text layouts like above.
- **Full API contract for every remaining CRUD endpoint** (facilities, menu items, shifts, notifications) — same pattern as Rooms (K.5) and Staff Invite (K.3) above; can be generated in bulk once you confirm the pattern here is right, rather than hand-writing ~40 more near-identical CRUD contracts now.
-->

