import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.data_manager import DataManager

class TestNewEventRegistrationFlow(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.dm = DataManager()

    def test_1_upcoming_events_with_options(self):
        response = self.client.post("/api/chat", json={"message": "What events are upcoming?"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("Would you like to register for any of these events?", data["answer"])
        self.assertEqual(data["intent"], "EVENT_INQUIRY")
        self.assertEqual(data["source"], "Events")
        self.assertIn("options", data)
        self.assertEqual(len(data["options"]), 5)
        self.assertIn("Register for Intro to GenAI Workshop", data["options"])

    def test_2_register_intro_to_genai_workshop_step1_name(self):
        req_payload = {
            "message": "Register for Intro to GenAI Workshop",
            "session_state": {}
        }
        res = self.client.post("/api/chat", json=req_payload).json()
        self.assertEqual(res["intent"], "ACTION_REQUEST")
        self.assertEqual(res["source"], "Agentic Workflow Engine")
        self.assertIn("Sure! I'll help you register for the Intro to GenAI Workshop. What is your name?", res["answer"])
        self.assertEqual(res["session_state"]["action_state"]["slots"]["event"], "Intro to GenAI Workshop")
        self.assertEqual(res["session_state"]["action_state"]["prompting"], "name")

    def test_3_step2_name_collection(self):
        req_payload = {
            "message": "Het",
            "session_state": {
                "user_memory": {},
                "action_state": {
                    "action_type": "Event Registration",
                    "slots": {"event": "Intro to GenAI Workshop"},
                    "prompting": "name"
                }
            }
        }
        res = self.client.post("/api/chat", json=req_payload).json()
        self.assertEqual(res["intent"], "ACTION_REQUEST")
        self.assertIn("Thanks, Het. What is your email address?", res["answer"])
        self.assertEqual(res["session_state"]["action_state"]["slots"]["name"], "Het")
        self.assertEqual(res["session_state"]["action_state"]["prompting"], "email")

    def test_4_step3_valid_email_completion_and_persistence(self):
        req_payload = {
            "message": "het@example.com",
            "session_state": {
                "user_memory": {"name": "Het"},
                "action_state": {
                    "action_type": "Event Registration",
                    "slots": {"event": "Intro to GenAI Workshop", "name": "Het"},
                    "prompting": "email"
                }
            }
        }
        res = self.client.post("/api/chat", json=req_payload).json()
        self.assertEqual(res["intent"], "ACTION_REQUEST")
        self.assertIn("Registration successful!", res["answer"])
        self.assertIn("Event: Intro to GenAI Workshop", res["answer"])
        self.assertIn("Name: Het", res["answer"])
        self.assertIn("Email: het@example.com", res["answer"])
        
        # Verify persistence in storage
        storage = self.dm.load_storage()
        reg_entries = storage.get("registrations", [])
        het_reg = [r for r in reg_entries if r.get("email") == "het@example.com" and r.get("event_title") == "Intro to GenAI Workshop"]
        self.assertTrue(len(het_reg) > 0, "Registration was not persisted in storage.json")

    def test_5_register_cloud_study_jam(self):
        res = self.client.post("/api/chat", json={"message": "Register me for Cloud Study Jam"}).json()
        self.assertEqual(res["intent"], "ACTION_REQUEST")
        self.assertIn("Sure! I'll help you register for the Cloud Study Jam. What is your name?", res["answer"])
        self.assertEqual(res["session_state"]["action_state"]["slots"]["event"], "Cloud Study Jam")

    def test_6_register_non_existent_event_rejection(self):
        res = self.client.post("/api/chat", json={"message": "Register me for AI Summit"}).json()
        self.assertEqual(res["intent"], "ACTION_REQUEST")
        self.assertIn("I don't see that event in the available club events.", res["answer"])
        self.assertIn("options", res)
        self.assertEqual(len(res["options"]), 5)

    def test_7_invalid_email_validation(self):
        req_payload = {
            "message": "not_an_email_format",
            "session_state": {
                "user_memory": {"name": "Het"},
                "action_state": {
                    "action_type": "Event Registration",
                    "slots": {"event": "Intro to GenAI Workshop", "name": "Het"},
                    "prompting": "email"
                }
            }
        }
        res = self.client.post("/api/chat", json=req_payload).json()
        self.assertIn("Please provide a valid email address.", res["answer"])
        self.assertEqual(res["session_state"]["action_state"]["prompting"], "email")

    def test_8_topic_switching_during_registration(self):
        req_payload = {
            "message": "Who leads AIML?",
            "session_state": {
                "user_memory": {},
                "action_state": {
                    "action_type": "Event Registration",
                    "slots": {"event": "Intro to GenAI Workshop"},
                    "prompting": "name"
                }
            }
        }
        res = self.client.post("/api/chat", json=req_payload).json()
        self.assertEqual(res["intent"], "FAQ")
        self.assertIn("Rahul Sharma", res["answer"])

    def test_9_dashboard_action_log(self):
        res = self.client.get("/api/dashboard/actions").json()
        regs = res.get("registrations", [])
        self.assertTrue(any(r["email"] == "het@example.com" for r in regs))

if __name__ == "__main__":
    unittest.main()
