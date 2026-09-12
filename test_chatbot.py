import unittest
from chatbot import get_bot_response, chatbot_instance
from app import app

class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_chatbot_varied_responses(self):
        """Test that chatbot returns varied, distinct, informative responses for different inputs"""
        queries = [
            "Hi there",
            "How much does a room cost?",
            "What is your check in time?",
            "What is your cancellation policy?",
            "What amenities do you offer?",
            "Tell me about dining and restaurant options"
        ]
        
        responses = set()
        for q in queries:
            res = get_bot_response(q, "test@example.com")
            self.assertIsNotNone(res)
            self.assertIn("response", res)
            response_text = res["response"].strip()
            self.assertTrue(len(response_text) > 10)
            responses.add(response_text)
        
        # Verify that all 6 queries received different responses (not the same single line!)
        self.assertEqual(len(responses), len(queries), "Chatbot should return unique, distinct answers for different queries")

    def test_api_chatbot_endpoint(self):
        """Test /api/chatbot POST endpoint returns valid JSON with dynamic response"""
        res = self.app.post('/api/chatbot', json={"message": "What are your check in times?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("2:00 PM", data.get("response"))

    def test_api_chatbot_greetings(self):
        """Test greeting response via /api/chatbot"""
        res = self.app.post('/api/chatbot', json={"message": "hello"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("intent"), "greeting")

    def test_api_chatbot_pricing(self):
        """Test pricing response via /api/chatbot"""
        res = self.app.post('/api/chatbot', json={"message": "how much is single room"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertTrue("₹" in data.get("response") or "rate" in data.get("response").lower() or "price" in data.get("response").lower())

if __name__ == '__main__':
    unittest.main()
