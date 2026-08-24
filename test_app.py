import unittest
from app.kb_engine import KnowledgeEngine
from app.intent_classifier import IntentClassifier
from app.data_manager import DataManager
from app.agent_engine import AgentEngine

class TestClubAssistantImprovements(unittest.TestCase):
    def setUp(self):
        self.dm = DataManager()
        self.clf = IntentClassifier()
        self.kb = KnowledgeEngine()
        self.agent = AgentEngine(self.dm)

    def test_01_greetings(self):
        intent, conf = self.clf.classify("Hello")
        self.assertEqual(intent, "GREETING")
        res = self.kb.query("Hello")
        self.assertIn("Hello!", res["answer"])
        self.assertEqual(res["source"], "Greeting")

    def test_02_strict_grounding_fallback(self):
        res = self.kb.query("What is the annual budget of GDG in 2030?")
        self.assertFalse(res["is_grounded"])
        self.assertEqual(res["answer"], "I don't have that information.")
        self.assertLess(res["confidence"], 0.45)

    def test_03_intent_classification_categories(self):
        self.assertEqual(self.clf.classify("Who leads AIML?")[0], "FAQ")
        self.assertEqual(self.clf.classify("When is the GenAI workshop?")[0], "EVENT_INQUIRY")
        self.assertEqual(self.clf.classify("Register me for GenAI Workshop")[0], "ACTION_REQUEST")
        self.assertEqual(self.clf.classify("random gibberish 123")[0], "UNKNOWN")

    def test_04_dynamic_source_citations(self):
        res1 = self.kb.query("Who leads AIML?")
        self.assertEqual(res1["source"], "Teams → AIML")

        res2 = self.kb.query("When is the GenAI workshop?")
        self.assertEqual(res2["source"], "Events → Intro to GenAI Workshop")

    def test_05_multi_turn_followups(self):
        history = [
            {"role": "user", "content": "Who leads AIML?"},
            {"role": "assistant", "content": "The lead for AIML is Rahul Sharma.", "subject": "Team:AIML"}
        ]
        res = self.kb.query("What about Web Dev?", history)
        self.assertIn("Priya Patel", res["answer"])
        self.assertEqual(res["source"], "Teams → Web Dev")

    def test_06_conversational_step_by_step_agent(self):
        session = {}
        # Turn 1
        r1 = self.agent.process_action("ACTION_REQUEST", "Register me for GenAI Workshop", session)
        self.assertFalse(r1["action_complete"])
        self.assertIn("full name", r1["answer"].lower())

        # Turn 2
        r2 = self.agent.process_action("ACTION_REQUEST", "Rahul Sharma", r1["session_state"])
        self.assertFalse(r2["action_complete"])
        self.assertIn("email address", r2["answer"].lower())

        # Turn 3
        r3 = self.agent.process_action("ACTION_REQUEST", "rahul@example.com", r2["session_state"])
        self.assertFalse(r3["action_complete"])
        self.assertIn("year", r3["answer"].lower())

        # Turn 4
        r4 = self.agent.process_action("ACTION_REQUEST", "2nd Year", r3["session_state"])
        self.assertTrue(r4["action_complete"])
        self.assertIn("REG-", r4["answer"])

if __name__ == "__main__":
    unittest.main()
