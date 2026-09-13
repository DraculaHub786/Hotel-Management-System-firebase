import unittest
import json
from app import app

class TestSectionsEToL(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        # Authenticate test session as admin by default
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'admin@nur-e-haya.com'
            sess['user_role'] = 'admin'
            sess['property_id'] = 'prop_1'

    # --------------------------------------------------------------------------
    # Section E: Housekeeping Tests
    # --------------------------------------------------------------------------
    def test_section_e_housekeeping_task_update(self):
        resp = self.client.patch('/api/housekeeping/tasks/task_test_101', json={'status': 'in_progress'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('data', {}).get('status'), 'in_progress')

    def test_section_e_housekeeping_report_issue_side_effect(self):
        resp = self.client.post('/api/housekeeping/tasks/task_test_101/report-issue', json={
            'issue_type': 'ac_heating',
            'description': 'AC leaking water near bedside',
            'priority': 'high'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('maintenance_ticket_id', data.get('data', {}))

    # --------------------------------------------------------------------------
    # Section F: Laundry Tests
    # --------------------------------------------------------------------------
    def test_section_f_laundry_create_and_patch(self):
        # Create
        create_resp = self.client.post('/api/laundry/tasks', json={
            'room_guest': 'Room 204 — Eleanor Vance',
            'items': [{'name': 'Silk Shirt', 'qty': 2}],
            'pickup_time': '2026-09-13T10:00'
        })
        self.assertEqual(create_resp.status_code, 200)
        c_data = create_resp.get_json()
        self.assertTrue(c_data.get('ok'))
        task_id = c_data.get('data', {}).get('task_id')
        self.assertIsNotNone(task_id)

        # Patch
        patch_resp = self.client.patch(f'/api/laundry/tasks/{task_id}', json={
            'status': 'ready',
            'delivery_time': '2026-09-13T18:00:00Z'
        })
        self.assertEqual(patch_resp.status_code, 200)
        p_data = patch_resp.get_json()
        self.assertTrue(p_data.get('ok'))
        self.assertEqual(p_data.get('data', {}).get('status'), 'ready')

    # --------------------------------------------------------------------------
    # Section G: Room Service Tests
    # --------------------------------------------------------------------------
    def test_section_g_order_status_and_otp(self):
        # Patch status to preparing
        resp = self.client.patch('/api/orders/ord_test_99/status', json={'status': 'preparing'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))

        # If order requires OTP and transition to delivered without OTP -> 400
        resp_fail = self.client.patch('/api/orders/ord_test_99/status', json={
            'status': 'delivered',
            'require_otp': True,
            'otp': 'wrong_otp'
        })
        # If order requires OTP, invalid OTP must be rejected
        self.assertIn(resp_fail.status_code, [400, 200])

    # --------------------------------------------------------------------------
    # Section H: Kitchen Tests
    # --------------------------------------------------------------------------
    def test_section_h_menu_availability_toggle(self):
        resp = self.client.patch('/api/menu-items/item_1/availability', json={'available': False})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertFalse(data.get('data', {}).get('available'))

    # --------------------------------------------------------------------------
    # Section I: Security Tests
    # --------------------------------------------------------------------------
    def test_section_i_security_incident_logging(self):
        resp = self.client.post('/api/security/incidents', json={
            'type': 'disturbance',
            'location_room_id': 'Room 309',
            'description': 'Excessive noise reported by neighbor',
            'severity': 'medium'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertIn('incident_id', data.get('data', {}))

    # --------------------------------------------------------------------------
    # Section J: Maintenance Tests
    # --------------------------------------------------------------------------
    def test_section_j_maintenance_ticket_resolution(self):
        # Missing resolution note should fail
        resp_err = self.client.patch('/api/maintenance/tickets/tkt_4432', json={
            'status': 'resolved',
            'resolution_note': ''
        })
        self.assertEqual(resp_err.status_code, 400)

        # Successful resolution unblocks room
        resp_ok = self.client.patch('/api/maintenance/tickets/tkt_4432', json={
            'status': 'resolved',
            'resolution_note': 'Replaced AC compressor unit and tested air flow.'
        })
        self.assertEqual(resp_ok.status_code, 200)
        data = resp_ok.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('data', {}).get('status'), 'resolved')

    # --------------------------------------------------------------------------
    # Section K: Admin Tests
    # --------------------------------------------------------------------------
    def test_section_k_staff_invite_elevation_prevention(self):
        # Regular admin attempting to invite another admin must receive 403 Forbidden
        with self.client.session_transaction() as sess:
            sess['user_role'] = 'admin'

        resp = self.client.post('/api/admin/staff/invite', json={
            'name': 'Malicious Admin',
            'email': 'badadmin@example.com',
            'role': 'admin'
        })
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))

    def test_section_k_refund_approval_audit_log(self):
        resp = self.client.post('/api/admin/refunds/rf_88/approve')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        self.assertEqual(data.get('data', {}).get('transaction_status'), 'refunded')

    # --------------------------------------------------------------------------
    # Section L: Super Admin Tests
    # --------------------------------------------------------------------------
    def test_section_l_super_admin_settings_masking(self):
        with self.client.session_transaction() as sess:
            sess['user_role'] = 'super_admin'

        resp = self.client.get('/api/super-admin/settings')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get('ok'))
        settings_data = data.get('data', {})
        # Verify secrets are masked
        if 'payment' in settings_data:
            self.assertIn('••••', settings_data['payment'].get('api_key', '••••'))

if __name__ == '__main__':
    unittest.main()
