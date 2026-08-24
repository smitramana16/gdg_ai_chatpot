import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.kb_engine import KnowledgeEngine
from app.intent_classifier import IntentClassifier
from app.data_manager import DataManager
from app.agent_engine import AgentEngine
from app.main import app
from fastapi.testclient import TestClient

class TestActionWorkflowAndMemory(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_bug_reproduction_and_fix(self):
        # 1. Start registration
        r1 = self.client.post("/api/chat", json={"message": "Register me for GenAI Workshop", "session_state": {}})
        d1 = r1.json()
        self.assertIn("name", d1["answer"].lower())

        # 2. User provides name "Het"
        r2 = self.client.post("/api/chat", json={"message": "Het", "session_state": d1["session_state"]})
        d2 = r2.json()
        self.assertIn("email", d2["answer"].lower())
        self.assertEqual(d2["session_state"]["user_memory"].get("name"), "Het")

        # 3. User asks: "you remember my name" (THE BUG CASE)
        r3 = self.client.post("/api/chat", json={"message": "you remember my name", "session_state": d2["session_state"]})
        d3 = r3.json()
        self.assertEqual(d3["intent"], "MEMORY_QUERY")
        self.assertIn("Het", d3["answer"])
        self.assertNotIn("email address for sending the ticket", d3["answer"].lower())
        print("\n[TEST 1 PASSED] Bug Fix Verified! Answer:", d3["answer"])

    def test_02_memory_queries(self):
        state = {"user_memory": {"name": "Het", "email": "het@example.com"}}
        
        # Name query
        r1 = self.client.post("/api/chat", json={"message": "Do you remember my name?", "session_state": state})
        self.assertIn("Het", r1.json()["answer"])

        # Email query
        r2 = self.client.post("/api/chat", json={"message": "Do you remember my email?", "session_state": state})
        self.assertIn("het@example.com", r2.json()["answer"])

        # Details query
        r3 = self.client.post("/api/chat", json={"message": "What details do you remember about me?", "session_state": state})
        self.assertIn("Het", r3.json()["answer"])
        self.assertIn("het@example.com", r3.json()["answer"])
        print("[TEST 2 PASSED] Memory Queries (Name, Email, Details) verified.")

    def test_03_workflow_interruption(self):
        # Start registration
        r1 = self.client.post("/api/chat", json={"message": "Register me for GenAI Workshop", "session_state": {}})
        d1 = r1.json()

        # User interrupts with FAQ query
        r2 = self.client.post("/api/chat", json={"message": "Who leads AIML?", "session_state": d1["session_state"]})
        d2 = r2.json()
        self.assertEqual(d2["intent"], "FAQ")
        self.assertIn("Rahul Sharma", d2["answer"])
        print("[TEST 3 PASSED] Workflow Interruption with FAQ query verified.")

    def test_04_workflow_cancellation(self):
        # Start registration
        r1 = self.client.post("/api/chat", json={"message": "Register me for GenAI Workshop", "session_state": {}})
        d1 = r1.json()

        # User cancels
        r2 = self.client.post("/api/chat", json={"message": "Cancel this.", "session_state": d1["session_state"]})
        d2 = r2.json()
        self.assertEqual(d2["intent"], "CANCEL")
        self.assertIn("cancelled", d2["answer"].lower())
        print("[TEST 4 PASSED] Workflow Cancellation verified.")

    def test_05_normal_faq_and_events(self):
        r1 = self.client.post("/api/chat", json={"message": "When was the club founded?"})
        self.assertIn("2022", r1.json()["answer"])

        r2 = self.client.post("/api/chat", json={"message": "Which event is on September 20?"})
        self.assertIn("Cloud Study Jam", r2.json()["answer"])

        r3 = self.client.post("/api/chat", json={"message": "What teams are available?"})
        self.assertIn("AIML", r3.json()["answer"])
        print("[TEST 5 PASSED] Normal FAQ and Events verified.")

if __name__ == "__main__":
    unittest.main()
