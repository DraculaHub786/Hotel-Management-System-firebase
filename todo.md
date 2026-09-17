# Nur-e-Haya — Master Plan: From Demo App to Real Multi-Tenant SaaS

**Audit date:** September 2026
**Current repo:** `DraculaHub786/Hotel-Management-System-firebase` (main, commit `7deb730`)
**Current stack:** Flask 3 (monolith, Blueprint-per-module) + Firestore + Jinja2 + vanilla JS, deployed on Render free tier via the Flask dev server.

This plan is split into three parts:
1. Security fixes (do these regardless of anything else — some are exploitable today)
2. The real-time / cross-role sync architecture you asked for
3. The phased roadmap to turn this into an actual multi-tenant SaaS product

---

## Part 0 — Confirmed Bugs & Root Causes (re-audited 2026-09-17, commit `8fe71db`)

The earlier version of this section listed symptoms. Tracing them further turned up root causes that explain why they keep recurring, and why the test suite doesn't catch them.

### 0.1 Root cause: rooms are seeded as duplicate documents
`data_seeder.py` writes **two separate Firestore documents per physical room**:
```
rooms_col.document(f"room_{number}").set(doc_data)      # e.g. "room_301"
rooms_col.document(f"rm_{flat_code}").set(doc_data)      # e.g. "rm_RW-301"
```
Nothing links these two documents after creation. Any endpoint that resolves a room by number/flat-code and updates it (front desk mark-clean, housekeeping task completion, room status board, night audit) may be reading or writing whichever of the two documents its particular fallback lookup happens to hit — while every *other* screen keeps reading the untouched copy. This is why an update can report success while the room's status appears unchanged elsewhere: it isn't one room with a lying UI, it's genuinely two database records for one room.
**Fix:** pick one canonical document ID per room (recommend the `flat_code`, since it's the human-meaningful, collision-proof identifier), migrate all existing data onto it, and delete the seeding duplication. Every route that currently does "try `.document(id)`, fall back to `.where(field, '==', id)`" should instead resolve to the canonical ID *once*, in a shared helper, not re-implemented per endpoint with slightly different field-name guesses each time.

### 0.2 Root cause: the test mock doesn't match real Firestore semantics
`MockDocumentReference.update()` in `app/firebase_db.py` silently **creates the document if it doesn't exist**. Real Firestore's `update()` does the opposite — it raises `NotFound` when the document isn't there. Every test that exercises an "update" endpoint is therefore validated against a database that is strictly more forgiving than production. This is a second, independent reason "it passes locally, breaks live" keeps happening — the safety net has a hole shaped exactly like this bug class.
**Fix:** make the mock's `update()` raise on a missing document, matching real Firestore, then re-run the full suite — expect more tests to fail immediately, which is the point: it means the suite starts catching what it's currently blind to. Longer term, run integration tests against the real Firebase emulator (not a hand-rolled mock) before this goes further.

### 0.3 Root cause: three different ID schemes for the same entity type
Menu items get zero-padded seed IDs (`item_001`), auto-generated Firestore IDs when added via the admin UI (`menu_col().add(data)`), and the test suite expects unpadded IDs (`item_1`) that no code path actually produces. None of these are reconciled, which is why the availability-toggle endpoint 404s on real data — same underlying problem as 0.1, just without the duplicate-document twist.
**Fix:** one ID generation strategy per collection, used everywhere that collection is written to — seeding, admin CRUD, and imports alike.

### 0.4 Broadcasting: persists and role-filters correctly, but isn't live
Announcements are written to Firestore and read back with genuinely correct role-targeting logic (`/api/announcements/active` filters by role sensibly). The gap is delivery: the frontend calls that endpoint exactly once, on `DOMContentLoaded`, and never again — no polling interval, no push, no "seen" state, and no expiry (an announcement from weeks ago is shown until it's pushed out of the most-recent-15 window). It functions like an inbox that never auto-refreshes, not a live broadcast.
**Fix (short-term, no new infra):** add a `setInterval` re-fetch (e.g. every 30–60s) and a `read_by` array on the announcement doc so a viewed announcement stops re-appearing per user. **Fix (real fix):** this is one of the first things that should ride on the websocket/pub-sub layer in Part 2 — a manager posting an announcement should push to every connected relevant-role client within a second, not wait for their next poll or reload.

### 0.5 Admin → staff invite: dispatch is fully fake
- `api_invite_staff()` hardcodes `"email_sent": True` — no email, SMS, or any delivery ever happens.
- `templates/admin/staff_invite.html` shows the admin a success toast ("Invitation dispatched to ...") and redirects away, **without ever surfacing the invite link/token anywhere in the UI** — there is currently no way for an admin to get the link to the new hire even manually.
- The invite token is `f"inv_{int(datetime.utcnow().timestamp())}"` — second-resolution only, so two invites created in the same second silently overwrite each other in Firestore.
**Fix:** (1) wire real delivery through the email provider from Part 3.4 (SendGrid/Postmark), (2) until that's live, surface the generated link in the admin UI with a copy button as an honest interim state instead of a fake success message, (3) generate the token with `secrets.token_urlsafe()` instead of a timestamp.

### 0.6 Confirmed test failures (symptoms of 0.1/0.3)
1. `POST /api/front-desk/mark-clean` — returns success, room status doc never actually flips (see 0.1). Confirmed by `test_e2e_workflows.py::test_frontdesk_mark_clean_endpoint`.
2. `PATCH /api/menu-items/<id>/availability` — 404s on real items (see 0.3). Confirmed by `test_sections_e_to_l.py::test_section_h_menu_availability_toggle`.

**Priority order for this section:** 0.1 and 0.2 first (they're the same disease behind most "it says success but nothing changed" bugs across *any* module, not just rooms/menu — audit every collection for the double-ID pattern and every mock method for real-vs-fake semantic drift before writing any more endpoints), then 0.3, then 0.4 and 0.5 in parallel since they're independent of the data-layer fix.

Also still unresolved from the original audit: **Google auth remains spoofable** (`/api/auth/google` trusts a client-supplied email; `google-auth` is installed but never called to verify a token).

---

## Part 1 — Security Fix List (pre-launch blockers)

| # | Issue | File | Fix |
|---|---|---|---|
| 1 | Google auth accepts any client-supplied email with no token verification | `app/auth/routes.py::google_auth_api` | Verify the `id_token` server-side via `google.oauth2.id_token.verify_oauth2_token`, using `GOOGLE_CLIENT_ID` as audience. Never trust a client-passed `email`. |
| 2 | `/api/transactions/<id>/simulate-pay` has no auth | `app/payments/routes.py` | Add `@login_required`, and restrict to the transaction's own owner or staff role. |
| 3 | Payment `amount` trusted from client | `app/payments/routes.py` | Recompute amount server-side from the booking/order record; never accept a client-supplied total for anything that finalizes a payment. |
| 4 | No CSRF protection | global | Add `Flask-WTF`'s CSRF extension (or a custom double-submit token) to every state-changing POST/PUT/DELETE. |
| 5 | Wide-open CORS, unused `ALLOWED_ORIGINS` | `app/__init__.py` | Read `ALLOWED_ORIGINS` from env and pass explicitly to `CORS(app, origins=[...], supports_credentials=True)`. |
| 6 | OTP returned in API response | `app/auth/otp_service.py`, `app/auth/routes.py` | Keep it in logs only (already done) behind a `DEMO_MODE=true` flag; strip `dev_otp` from the JSON response entirely once a real SMS/email provider is wired in. |
| 7 | No rate limit on OTP resend/verify | `app/auth/routes.py` | Add per-email/IP limits (5 OTP requests / 15 min) via Flask-Limiter backed by Redis. |
| 8 | Dead plaintext/SHA-256 fallback in password check | `app/auth/routes.py::verify_password` | Delete the fallback branches; bcrypt only. |
| 9 | In-memory rate limiting | `app/auth/routes.py` | Move to Redis so it survives restarts and works across multiple workers/instances. |
| 10 | Dev server used as the production server | `Procfile`, `render.yaml` | Run behind Gunicorn (`gunicorn -w 4 -k gthread app:app`) or Uvicorn+ASGI if you migrate to FastAPI. |
| 11 | `SECRET_KEY` randomized per process if unset | `config.py` | Require it from env in production; fail startup if missing. |

None of these require an architecture change — they're a focused 1–2 week hardening sprint before Part 3 even starts.

---

## Part 2 — Real-Time Cross-Role Sync Architecture

Right now every screen (guest, front desk, kitchen, housekeeping, admin, etc.) is a server-rendered Jinja page that only updates on reload/polling. To make "all screens and user types synced for fast data updates" actually true, you need a push layer, not more polling.

**Recommended pattern: Firestore realtime listeners → WebSocket fan-out → thin reactive frontend**

```
Firestore (source of truth)
   │  onSnapshot listeners (server-side, per collection)
   ▼
Sync Service (Node/Python worker)
   │  publishes typed events: booking.created, order.status_changed,
   │                          room.status_changed, payment.completed, ...
   ▼
WebSocket Gateway (Socket.IO or native WS, one gateway, room-scoped)
   │  rooms = tenant_id + role (e.g. "prop_1:kitchen", "prop_1:frontdesk",
   │           "prop_1:guest:<user_id>")
   ▼
Frontend clients subscribe to their own room(s) only
```

Concretely:
- Keep Firestore as the durable store (it already has good realtime primitives — you're just not using them yet).
- Add a lightweight **event bus**: either (a) use Firestore's own `onSnapshot` from a small always-on Node/Python service that re-publishes changes to Socket.IO, or (b) move truly hot paths (order queue, room status board, kitchen KDS) into **Firebase Realtime Database** or **Redis Pub/Sub**, which are cheaper to fan out than Firestore snapshot listeners at scale.
- Every role dashboard (kitchen queue, housekeeping board, front desk board, guest "my booking" page) subscribes only to the events relevant to its `property_id` + role — this is what keeps it fast: nobody receives updates they don't need.
- For the guest side specifically: a booking status change, payment confirmation, or order update should push to the guest's open tab within under a second, not on next page load.
- Keep a REST/JSON API (what you already have) for all writes and initial page loads; use the WebSocket layer purely for push notifications of state changes, not as the primary data path. This keeps the system debuggable and lets you degrade gracefully to polling if a socket drops.

This is the single biggest architectural gap in the current app, and it's also the most valuable one to fix, since it's what makes the product feel like a real hotel PMS instead of a form-and-refresh app.

---

## Part 3 — SaaS Transformation Roadmap

### 3.1 Multi-tenancy (the core SaaS shift)
The schema already has a `property_id` field on users (`prop_1`), which means someone was already thinking about this — but it isn't enforced anywhere. Every collection query (`rooms_col()`, `bookings_col()`, etc.) currently returns data across *all* properties.

- Add `tenant_id` (rename/reuse `property_id`) to every document in every collection.
- Enforce it at the query layer: build a `scoped_collection(tenant_id, name)` helper that every route uses instead of calling `*_col()` directly, so it's structurally impossible to forget the filter.
- Add a `tenants` collection: plan tier, billing status, feature flags, branding (logo/colors), custom domain/subdomain.
- Route resolution: `hotelname.yourapp.com` or `/t/<tenant_slug>/...` → resolves `tenant_id` before anything else runs.

### 3.2 Backend architecture
- Move off the Flask dev server → Gunicorn/Uvicorn with multiple workers, behind a reverse proxy (Nginx or the platform's built-in one).
- Introduce **Redis** for: session store (so sessions survive restarts and scale across workers), rate limiting, and pub/sub for the realtime layer above.
- Introduce a **background job queue** (Celery or RQ) for anything that shouldn't block a request: sending emails/SMS OTPs, generating invoices/PDFs, nightly audits, report generation.
- Keep the current Blueprint-per-module structure — it maps cleanly to your 13 modules — but tighten it into a proper layered structure per module: `routes.py` (HTTP only) → `service.py` (business logic) → `repository.py` (Firestore access). Right now routes talk to Firestore directly, which makes testing and reuse harder as it grows.
- Add structured logging (JSON logs) and error tracking (Sentry) — right now errors only go to stdout.

### 3.3 Payments (real, not simulated)
- Integrate a real gateway for the Indian market: **Razorpay** or **Cashfree** (both have UPI, cards, netbanking, and India-specific compliance out of the box) instead of the fake QR/UPI string generator.
- Server creates an order via the gateway API → client completes payment via their SDK/checkout → gateway sends a **signed webhook** back to you → you verify the signature and only then mark the transaction complete. This closes vulnerability #2/#3 above by construction — the server never trusts client-reported payment status.
- Keep a `DEMO_MODE` flag that swaps in the current simulate-pay flow for staging/demo environments, gated behind the auth fix from Part 1.

### 3.4 OTP / notifications (real, not simulated)
- Swap the "log it and return it" OTP delivery for a real provider: **MSG91** or **Twilio Verify** for SMS, **SendGrid/Postmark** for email — both are trivial to drop into `otp_service.py` since it already isolates generation/verification from delivery.
- Same `DEMO_MODE` pattern: in demo/staging, keep logging + returning it for convenience; in production, delivery goes out over the real channel and the code is never in the response body.

### 3.5 Data & search
- Firestore is fine as the primary store, but add **Algolia** or **Meilisearch** for guest-facing room/facility search and admin search-across-bookings — Firestore's query model doesn't do full-text or multi-field ranked search well.
- Add a nightly export to a warehouse (BigQuery, since you're already GCP-adjacent) once you need real analytics/reporting beyond simple sums — the current revenue dashboard just streams every transaction document and sums in Python, which won't scale past a few thousand rows.

### 3.6 Testing & CI/CD
- You already have `test_*.py` files and a GitHub Actions workflow — extend it: add a staging Firebase project, run the full suite against it on every PR, and add contract tests for the payment webhook and OTP flow specifically since those are the highest-risk paths.
- Add pre-commit hooks (linting, secret-scanning) so credentials/API keys can't land in a commit — the repo history shows several commits specifically fixing Firebase-credential handling, which suggests this has already bitten you once.

### 3.7 Frontend
- Current Jinja2 + vanilla JS is fine for staff back-office screens (fast to build, low overhead) — don't rewrite those.
- For guest-facing and any screen that needs the realtime sync from Part 2 (booking status, kitchen queue, housekeeping board, front desk board), migrate incrementally to a small reactive layer — Alpine.js or htmx if you want to stay lightweight and keep server-rendered HTML, or React/Vue islands if you want a richer client. Given the scope (90 screens), htmx + Alpine.js is the pragmatic choice: it lets you keep 90% of your existing templates and just add live-update behavior where it matters, rather than a full SPA rewrite.

### 3.8 Ops & observability
- Move off Render free tier for anything beyond demo: it sleeps on inactivity and the free plan doesn't give you the persistent Redis/worker processes the above needs. Render's paid tier, Railway, or Fly.io all work; a full move to AWS/GCP only makes sense once you have real multi-region or compliance requirements.
- Add uptime monitoring + alerting (UptimeRobot/Better Uptime) on `/api/health`, and dashboards for: request latency, error rate, OTP delivery success rate, payment webhook success rate.

---

## Part 4 — Employee Coverage & Screen Completeness Audit

This part addresses two specific gaps found in the current build: missing digital onboarding for several real hotel employee types, and screens that render but don't actually save anything.

### 4.1 The real staff roster a hotel needs (vs. what's wired today)

| Employee type | Route/permission exists? | Seed account exists? | Can actually get a login today? |
|---|---|---|---|
| Admin / Super Admin | Yes | Yes | Yes |
| Manager | Yes | Yes | Yes |
| Front Desk | Yes | Yes | Yes |
| Housekeeping | Yes | Yes | Yes |
| Laundry | Yes | Yes | Yes |
| Maintenance / Engineering | Yes | Yes | Yes |
| Concierge | Yes | Yes | Yes |
| Accountant | Yes | Yes | Yes |
| Chef | Yes | Yes | Yes |
| **Kitchen staff (non-chef)** | Yes (`role_required` accepts `kitchen`) | **No** | **No** |
| **Waiter** | Yes (`/dining/tables`, `/staff/room-service`) | **No** | **No** |
| **Room service staff** | Yes | **No** | **No** |
| **Security** | Yes (`/staff/security`) | **No** | **No** |
| **Cashier** | Yes (`/dining/tables` permission) | **No** | **No** |
| Bellhop / Porter | Not modeled at all | No | No |
| Spa / Gym / Wellness staff | Screens exist (guest-facing booking), no staff-side operator role | No | No |
| Valet / Parking attendant | Screen exists (`/security/parking`) but folded under `security` role only | No | No |

**Root cause:** account creation is only wired for two paths — (1) guest self-registration, hardcoded to `role in ['member','guest','user']`, and (2) manual Firestore seeding at app startup. The admin "invite staff" endpoint writes a token but nothing ever redeems it.

**Fix — build the missing half of the invite flow:**
1. `GET /invite/<token>` — public page: shows the invited email + assigned role, lets them set a name + password.
2. `POST /api/invite/<token>/accept` — validates the token (unused, not expired), creates the actual `users` doc with the invited `role`/`staff_role`, marks the invite `used: true`, logs the person in.
3. Send the invite link by email (same provider you wire in for OTP delivery — Part 3.4) instead of only generating a token silently.
4. Extend `init_seed_users()` (or better, a one-time `scripts/seed_demo_staff.py`) to add demo accounts for `kitchen`, `waiter`, `room_service`, `security`, `cashier` so every role in the permission matrix is actually testable today, not just in theory.
5. Add the missing roles that aren't modeled at all yet — bellhop/porter, spa/gym operator, valet/parking attendant as its own `staff_role` distinct from general `security` — each gets its own task queue screen following the same pattern as housekeeping/laundry (see 4.2).

### 4.2 Standard "screen contract" — so nothing stays half-built again

The uneven quality isn't random — every *fully working* module (housekeeping, laundry, maintenance, security incidents, kitchen orders) follows the same shape, and every *hollow* one (dining tables, events calendar/catering/enquiries, manager calendar, CRM loyalty/memberships) skips part of it. Standardize this as a checklist every module must satisfy before it's considered "done," and re-run it against the confirmed hollow screens:

A screen is only complete when it has all four:
1. **GET route** that renders real Firestore data (not just a hardcoded fallback list).
2. **POST/PATCH API route** that persists the action the UI offers (status change, assignment, approval, etc.).
3. **Frontend JS that calls that API** and only shows a success toast after a real 200 response — never a fake `setTimeout` + reload.
4. **Role-gated + audit-logged**, consistent with `role_required` and `log_audit_denied` already used elsewhere.

**Known screens currently failing this checklist (fix in this order — highest guest/staff visibility first):**
1. `/dining/tables` — waiter table status (needs `PATCH /api/dining/tables/<table_no>`)
2. `/events/calendar` — event scheduling (needs create/update endpoints for banquet/spa/gym bookings feeding the calendar)
3. `/manager/calendar` — likely just needs to read from the same events data once 4.2.2 is fixed
4. `/events/catering`, `/events/enquiries` — needs POST endpoints for creating/responding to enquiries and selecting catering packages
5. `/crm/loyalty`, `/crm/memberships` — needs POST endpoints for manually adjusting points/tier (staff-initiated) and a proper points-accrual hook on completed bookings/orders (system-initiated)

Treat this table as a living checklist — run it against every screen in `todo.md` before marking a module "done," not just the ones flagged here.

---

## Suggested Phasing

| Phase | Focus | Rough effort |
|---|---|---|
| 0 | Security fix list (Part 1) | 1–2 weeks |
| 0.5 | Finish staff invite-accept flow + seed missing roles (Part 4.1); fix the 5 hollow screens (Part 4.2) | 1–2 weeks |
| 1 | Redis (sessions, rate limits) + Gunicorn + structured logging | 1 week |
| 2 | Realtime sync layer (Part 2) for the highest-value screens: kitchen queue, front desk board, housekeeping board, guest booking status | 2–3 weeks |
| 3 | Multi-tenancy enforcement (`tenant_id` everywhere + scoped queries) | 2 weeks |
| 4 | Real payment gateway integration + webhook verification | 1–2 weeks |
| 5 | Real OTP/notification delivery | 3–5 days |
| 6 | Background jobs (Celery/RQ) for invoices, night audit, reports | 1 week |
| 7 | Search (Algolia/Meilisearch) + analytics export | 1–2 weeks |
| 8 | CI/CD hardening, monitoring, staging environment | ongoing |

This keeps the current module structure and 13-domain design intact — it's genuinely a solid product scope — while replacing the parts that were built as demo shortcuts (in-memory rate limits, fake payment confirmation, unauthenticated Google login, dev server) with the equivalents a real SaaS needs.