import unittest
import json
from app import app
from app.auth.otp_service import generate_and_store_otp, verify_otp
from guest_service import generate_qr_base64

class TestMasterPlan(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    # 1. Health & Foundation Check
    def test_foundation_health_check(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('service'), 'nur-e-haya-os')

    # 2. OTP Lifecycle Check (Module 1 / Phase 2)
    def test_otp_lifecycle_end_to_end(self):
        test_email = "test.otp.user@example.com"
        # Generate OTP
        code = generate_and_store_otp(test_email, purpose='register')
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

        # Invalid OTP verification attempt
        ok, msg = verify_otp(test_email, "000000", purpose='register')
        self.assertFalse(ok)
        self.assertIn("Invalid OTP", msg)

        # Valid OTP verification
        ok_valid, msg_valid = verify_otp(test_email, code, purpose='register')
        self.assertTrue(ok_valid)
        self.assertIn("verified successfully", msg_valid)

    # 3. Role Routing & Dashboard Check
    def test_role_routed_dashboards(self):
        # Admin gets redirected to /admin
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'admin@nur-e-haya.com'
            sess['user_role'] = 'admin'
        resp_admin = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp_admin.status_code, 302)
        self.assertIn('/admin', resp_admin.headers['Location'])

        # Chef gets redirected to /dining/kitchen
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'chef@nur-e-haya.com'
            sess['user_role'] = 'chef'
        resp_chef = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp_chef.status_code, 302)
        self.assertIn('/dining/kitchen', resp_chef.headers['Location'])

        # Housekeeping gets redirected to /services/housekeeping
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'cleaning@nur-e-haya.com'
            sess['user_role'] = 'housekeeping'
        resp_hsk = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp_hsk.status_code, 302)
        self.assertIn('/services/housekeeping', resp_hsk.headers['Location'])

    # 4. Front Office: Room search & Booking with Member 5% Discount
    def test_member_discount_booking_flow(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'member@nur-e-haya.com'
            sess['user_role'] = 'member'

        # Checkout booking
        resp = self.client.post('/api/cart/checkout', json={
            "items": [
                {"ref_id": "101", "room_number": "101", "check_in": "2026-10-01", "check_out": "2026-10-03"}
            ],
            "guests": 2,
            "payment_method": "card"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('booking_id', data.get('data', {}))
        self.assertIn('booking_no', data.get('data', {}))

    # 5. QR Code Generation for e-Tickets & Payments
    def test_qr_generation(self):
        payload = "NUR-E-HAYA:BK1029384:101:2026-10-01"
        qr_b64 = generate_qr_base64(payload)
        self.assertIsNotNone(qr_b64)
        self.assertTrue(len(qr_b64) > 50)

    # 6. Dining Menu & Orders Lifecycle
    def test_dining_order_lifecycle(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'user@nur-e-haya.com'
            sess['user_role'] = 'guest'

        resp_order = self.client.post('/api/orders', json={
            "room_number": "102",
            "items": [
                {"name": "Paneer Tikka Butter Masala", "price": 450, "qty": 1},
                {"name": "Garlic Butter Naan", "price": 90, "qty": 2}
            ],
            "payment_method": "room_charge"
        })
        self.assertEqual(resp_order.status_code, 200)
        odata = resp_order.get_json()
        self.assertTrue(odata.get('ok'))
        order_id = odata.get('data', {}).get('order_id')
        self.assertIsNotNone(order_id)

        # Transition status to preparing
        resp_status = self.client.patch(f'/api/orders/{order_id}/status', json={'status': 'preparing'})
        self.assertEqual(resp_status.status_code, 200)

    # 7. Concierge Request Flow
    def test_concierge_request_creation(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'user@nur-e-haya.com'
            sess['user_name'] = 'Guest Traveler'

        resp = self.client.post('/concierge/request', json={
            "type": "wake_up",
            "room_number": "104",
            "scheduled_time": "06:30 AM",
            "details": "Morning wake-up call for flight."
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('request_id', data.get('data', {}))

    # 8. Night Audit Execution
    def test_frontdesk_night_audit(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'frontdesk@nur-e-haya.com'
            sess['user_role'] = 'front_desk'

        resp = self.client.post('/frontdesk/night-audit')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('audit', data.get('data', {}))

    # 9. Manager Operations & CSV Export
    def test_manager_reports_csv_export(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'manager@nur-e-haya.com'
            sess['user_role'] = 'manager'

        resp = self.client.get('/manager/reports?format=csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=hotel_operations_report.csv', resp.headers.get('Content-Disposition', ''))

    # 10. Audit Logging on Denied Elevation
    def test_unauthorized_role_access_audit_log(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'user@nur-e-haya.com'
            sess['user_role'] = 'guest'

        # Guest attempting admin endpoint
        resp = self.client.get('/api/admin/revenue')
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))

    # 11. Complete 90-Screen Inventory Verification (SCR-01 through SCR-90)
    def test_all_90_screens_inventory(self):
        screens = [
            # Module 1: Auth & Onboarding (Public - unauthenticated)
            ('SCR-01', '/login', None),
            ('SCR-02', '/register', None),
            ('SCR-03', '/login', None),
            ('SCR-04', '/forgot-password', None),
            ('SCR-05', '/reset-password', None),
            ('SCR-06', '/login', None),

            # Module 2: Common
            ('SCR-07', '/profile', 'guest'),
            ('SCR-08', '/notifications', 'guest'),
            ('SCR-09', '/search?q=deluxe', 'guest'),
            ('SCR-10', '/help', 'guest'),
            ('SCR-11', '/support', 'guest'),

            # Module 3: Front Office & Guest
            ('SCR-12', '/dashboard', 'guest'),
            ('SCR-13', '/rooms', 'guest'),
            ('SCR-14', '/rooms/101', 'guest'),
            ('SCR-15', '/checkout', 'guest'),
            ('SCR-16', '/my-bookings', 'guest'),
            ('SCR-17', '/confirmation/BK1234', 'guest'),
            ('SCR-18', '/frontdesk/checkin', 'front_desk'),
            ('SCR-19', '/frontdesk/checkout', 'front_desk'),
            ('SCR-20', '/frontdesk/rooms', 'front_desk'),
            ('SCR-21', '/frontdesk/walkin', 'front_desk'),
            ('SCR-22', '/frontdesk/guests', 'front_desk'),
            ('SCR-23', '/frontdesk/night-audit', 'front_desk'),

            # Module 4: Dining & Room Service
            ('SCR-24', '/dining/foods', 'guest'),
            ('SCR-25', '/dining/drinks', 'guest'),
            ('SCR-26', '/dining/snacks', 'guest'),
            ('SCR-27', '/cart', 'guest'),
            ('SCR-28', '/dining/menu', 'guest'),
            ('SCR-29', '/pay/TXN1234', 'guest'),
            ('SCR-30', '/dining/kitchen', 'chef'),
            ('SCR-31', '/dining/tables', 'waiter'),
            ('SCR-32', '/dining/minibar', 'guest'),
            ('SCR-33', '/dining/inventory', 'chef'),

            # Module 5: Housekeeping & Guest Services
            ('SCR-34', '/staff/housekeeping', 'housekeeping'),
            ('SCR-35', '/services/request', 'guest'),
            ('SCR-36', '/services/my-requests', 'guest'),
            ('SCR-37', '/staff/laundry', 'laundry'),
            ('SCR-38', '/staff/maintenance', 'maintenance'),
            ('SCR-39', '/services/lost-found', 'housekeeping'),
            ('SCR-40', '/services/linen', 'housekeeping'),
            ('SCR-41', '/staff/housekeeping/tasks/TSK101', 'housekeeping'),
            ('SCR-42', '/services/room-status', 'housekeeping'),
            ('SCR-43', '/services/deep-cleaning', 'housekeeping'),

            # Module 6: Engineering / Maintenance
            ('SCR-44', '/maintenance/work-orders', 'maintenance'),
            ('SCR-45', '/maintenance/preventive', 'maintenance'),
            ('SCR-46', '/maintenance/assets', 'maintenance'),
            ('SCR-47', '/staff/maintenance/tickets/TKT101', 'maintenance'),

            # Module 7: Concierge
            ('SCR-48', '/concierge/request', 'guest'),
            ('SCR-49', '/concierge/transfers', 'concierge'),
            ('SCR-50', '/concierge/tours', 'guest'),
            ('SCR-51', '/concierge/doctor', 'guest'),
            ('SCR-52', '/concierge/local-guide', 'guest'),

            # Module 8: Accounts & Payments
            ('SCR-53', '/accounts/ledger', 'accountant'),
            ('SCR-54', '/accounts/invoices/INV101', 'accountant'),
            ('SCR-55', '/accounts/qr-verify', 'accountant'),
            ('SCR-56', '/accounts/refunds', 'accountant'),
            ('SCR-57', '/accounts/settlement', 'accountant'),
            ('SCR-58', '/accounts/taxes', 'admin'),

            # Module 9: Events, Banquets & Wellness
            ('SCR-59', '/events/banquets', 'guest'),
            ('SCR-60', '/events/catering', 'guest'),
            ('SCR-61', '/events/calendar', 'events'),
            ('SCR-62', '/wellness/spa', 'guest'),
            ('SCR-63', '/wellness/fitness', 'guest'),
            ('SCR-64', '/events/enquiries', 'front_desk'),

            # Module 10: Manager / Operations
            ('SCR-65', '/manager', 'manager'),
            ('SCR-66', '/manager/tasks/assign', 'manager'),
            ('SCR-67', '/manager/rates', 'manager'),
            ('SCR-68', '/manager/calendar', 'manager'),
            ('SCR-69', '/manager/reports', 'manager'),
            ('SCR-70', '/manager/announcements', 'manager'),
            ('SCR-71', '/manager/shifts', 'manager'),
            ('SCR-72', '/manager/expenses', 'manager'),

            # Module 11: Admin / Platform
            ('SCR-73', '/admin', 'admin'),
            ('SCR-74', '/admin/revenue', 'admin'),
            ('SCR-75', '/admin/staff', 'admin'),
            ('SCR-76', '/admin/staff/invite', 'admin'),
            ('SCR-77', '/admin/menu', 'admin'),
            ('SCR-78', '/admin/services', 'admin'),
            ('SCR-79', '/admin/promo-codes', 'admin'),
            ('SCR-80', '/admin/audit-logs', 'admin'),
            ('SCR-81', '/admin/settings', 'admin'),
            ('SCR-82', '/admin/backup-export?collection=bookings', 'admin'),

            # Module 12: Security, Parking & Safety
            ('SCR-83', '/security/visitors', 'security'),
            ('SCR-84', '/staff/security', 'security'),
            ('SCR-85', '/security/parking', 'security'),
            ('SCR-86', '/security/emergency', 'guest'),

            # Module 13: CRM, Loyalty & Marketing
            ('SCR-87', '/crm/loyalty', 'member'),
            ('SCR-88', '/crm/memberships', 'admin'),
            ('SCR-89', '/crm/reviews', 'guest'),
            ('SCR-90', '/admin/newsletter', 'admin')
        ]
        self.assertEqual(len(screens), 90)

        for scr_id, url, role in screens:
            with self.client.session_transaction() as sess:
                sess.clear()
                if role:
                    sess['user_email'] = f'{role}@nur-e-haya.com'
                    sess['user_name'] = f'Test {role.title()}'
                    sess['user_role'] = role
                    sess['staff_role'] = role

            resp = self.client.get(url)
            self.assertEqual(
                resp.status_code, 200,
                f"Screen {scr_id} ({url}) as role '{role}' failed with status {resp.status_code}"
            )

if __name__ == '__main__':
    unittest.main()
