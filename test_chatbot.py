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

    def test_api_chatbot_message_and_facility_intents(self):
        """Test dashboard /api/chatbot/message endpoint and facility recognition"""
        # Spa inquiry
        res_spa = self.app.post('/api/chatbot/message', json={"message": "Tell me about the spa and Ayurvedic massage"})
        self.assertEqual(res_spa.status_code, 200)
        data_spa = res_spa.get_json()
        self.assertTrue(data_spa.get("success"))
        self.assertEqual(data_spa.get("intent"), "spa_wellness")
        self.assertIn("The Royal Ayur Spa", data_spa.get("response"))

        # Pool inquiry
        res_pool = self.app.post('/api/chatbot/message', json={"message": "What time does the swimming pool open?"})
        self.assertEqual(res_pool.status_code, 200)
        data_pool = res_pool.get_json()
        self.assertTrue(data_pool.get("success"))
        self.assertEqual(data_pool.get("intent"), "pool_cabana")
        self.assertIn("pool", data_pool.get("response").lower())

        # Gym inquiry
        res_gym = self.app.post('/api/chatbot/message', json={"message": "Is the gym open 24/7?"})
        self.assertEqual(res_gym.status_code, 200)
        data_gym = res_gym.get_json()
        self.assertTrue(data_gym.get("success"))
        self.assertEqual(data_gym.get("intent"), "fitness_sauna")

    def test_api_chatbot_suggestions_and_history(self):
        """Test /api/chatbot/suggestions and /api/chatbot/history endpoints"""
        # Suggestions
        res_sug = self.app.get('/api/chatbot/suggestions')
        self.assertEqual(res_sug.status_code, 200)
        data_sug = res_sug.get_json()
        self.assertTrue(data_sug.get("success"))
        self.assertTrue(len(data_sug.get("suggestions", [])) >= 4)

        # History
        res_hist = self.app.get('/api/chatbot/history')
        self.assertEqual(res_hist.status_code, 200)
        data_hist = res_hist.get_json()
        self.assertTrue(data_hist.get("success"))
        self.assertIsInstance(data_hist.get("history"), list)

    def test_api_chatbot_transfer(self):
        """Test /api/chatbot/transfer human concierge escalation"""
        res_trans = self.app.post('/api/chatbot/transfer', json={
            "reason": "Need human support for special event booking"
        })
        self.assertEqual(res_trans.status_code, 200)
        data_trans = res_trans.get_json()
        self.assertTrue(data_trans.get("success"))

if __name__ == '__main__':
    unittest.main()
