import unittest
import time
from app import is_valid_password, is_valid_staff_password, check_login_rate_limit, record_failed_login, clear_failed_login, get_role_redirect

class TestSectionB(unittest.TestCase):
    def test_password_policy(self):
        # Guest password: min 8 chars
        self.assertTrue(is_valid_password("12345678"))
        self.assertFalse(is_valid_password("short"))

        # Staff password: min 10 chars, 1 number, 1 symbol
        self.assertTrue(is_valid_staff_password("Secret10@#"))
        self.assertFalse(is_valid_staff_password("short1@"))      # < 10 chars
        self.assertFalse(is_valid_staff_password("NoNumberSymbol!")) # no number
        self.assertFalse(is_valid_staff_password("NoSymbol12345"))   # no symbol

    def test_role_redirects(self):
        self.assertEqual(get_role_redirect('admin'), '/admin')
        self.assertEqual(get_role_redirect('front_desk'), '/staff/front-desk')
        self.assertEqual(get_role_redirect('housekeeping'), '/staff/housekeeping')
        self.assertEqual(get_role_redirect('kitchen'), '/staff/kitchen')
        self.assertEqual(get_role_redirect('laundry'), '/staff/laundry')
        self.assertEqual(get_role_redirect('guest'), '/dashboard')

    def test_rate_limiting(self):
        test_key = "127.0.0.1:test_ratelimit@example.com"
        clear_failed_login(test_key)

        for _ in range(4):
            record_failed_login(test_key)
        
        blocked, _ = check_login_rate_limit(test_key)
        self.assertFalse(blocked)

        # 5th attempt triggers rate limit
        record_failed_login(test_key)
        blocked, mins = check_login_rate_limit(test_key)
        self.assertTrue(blocked)
        self.assertGreaterEqual(mins, 1)

        clear_failed_login(test_key)
        blocked, _ = check_login_rate_limit(test_key)
        self.assertFalse(blocked)

    def test_google_auth_validation(self):
        from app import app
        client = app.test_client()
        resp = client.post('/api/google-auth', json={})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get('ok'))
        self.assertIn("Invalid Google authentication data", data.get('message', ''))

if __name__ == '__main__':
    unittest.main()
