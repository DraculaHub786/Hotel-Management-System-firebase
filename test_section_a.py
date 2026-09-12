import unittest
import json
from flask import Flask
from api_utils import api_success, api_error, permission_denied

class TestSectionA(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_api_success_envelope(self):
        with self.app.test_request_context():
            resp, status = api_success({"user": "test", "id": 123})
            data = json.loads(resp.get_data(as_text=True))
            self.assertEqual(status, 200)
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("data", {}).get("user"), "test")

    def test_api_error_envelope(self):
        with self.app.test_request_context():
            resp, status = api_error(errors={"email": "Invalid format"}, message="Validation failed", status=422)
            data = json.loads(resp.get_data(as_text=True))
            self.assertEqual(status, 422)
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("message"), "Validation failed")
            self.assertEqual(data.get("errors", {}).get("email"), "Invalid format")

    def test_permission_denied_envelope(self):
        with self.app.test_request_context():
            resp, status = permission_denied()
            data = json.loads(resp.get_data(as_text=True))
            self.assertEqual(status, 403)
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("message"), "You do not have permission to perform this action.")

if __name__ == '__main__':
    unittest.main()
