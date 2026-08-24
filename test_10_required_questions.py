import sys
import unittest

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.kb_engine import KnowledgeEngine
from app.intent_classifier import IntentClassifier
from app.data_manager import DataManager
from app.agent_engine import AgentEngine

class TestRequired10Questions(unittest.TestCase):
    def setUp(self):
        self.dm = DataManager()
        self.clf = IntentClassifier()
        self.kb = KnowledgeEngine()
        self.agent = AgentEngine(self.dm)

    def test_01_available_teams(self):
        intent, _ = self.clf.classify("What teams are available?")
        res = self.kb.query("What teams are available?")
        self.assertIn(intent, ["FAQ", "GREETING"])
        self.assertTrue(res["is_grounded"])
        self.assertIn("AIML", res["answer"])
        self.assertIn("Web Dev", res["answer"])
        self.assertEqual(res["source"], "Teams")
        self.assertGreaterEqual(res["confidence"], 0.90)
        print("[TEST 1 PASSED] What teams are available? -> Intent:", intent, "| Source:", res["source"], "| Conf:", res["confidence"])

    def test_02_who_leads_aiml(self):
        intent, _ = self.clf.classify("Who leads AIML?")
        res = self.kb.query("Who leads AIML?")
        self.assertEqual(intent, "FAQ")
        self.assertTrue(res["is_grounded"])
        self.assertIn("Rahul Sharma", res["answer"])
        self.assertEqual(res["source"], "Teams → AIML")
        self.assertGreaterEqual(res["confidence"], 0.90)
        print("[TEST 2 PASSED] Who leads AIML? -> Answer: Rahul Sharma | Source:", res["source"])

    def test_03_who_leads_it(self):
        history = [
            {"role": "user", "content": "Tell me about Web Dev team"},
            {"role": "assistant", "content": "Web Dev lead is Priya Patel", "subject": "Team:Web Dev"}
        ]
        res = self.kb.query("Who leads it?", history)
        self.assertTrue(res["is_grounded"])
        self.assertIn("Priya Patel", res["answer"])
        self.assertEqual(res["source"], "Teams → Web Dev")
        print("[TEST 3 PASSED] Who leads it? (Multi-turn) -> Answer: Priya Patel | Source:", res["source"])

    def test_04_when_was_club_founded(self):
        intent, _ = self.clf.classify("When was the club founded?")
        res = self.kb.query("When was the club founded?")
        self.assertEqual(intent, "FAQ")
        self.assertTrue(res["is_grounded"])
        self.assertIn("2022", res["answer"])
        self.assertEqual(res["source"], "Club Introduction")
        self.assertGreaterEqual(res["confidence"], 0.90)
        print("[TEST 4 PASSED] When was the club founded? -> Answer: 2022 | Source:", res["source"])

    def test_05_upcoming_events(self):
        intent, _ = self.clf.classify("What events are upcoming?")
        res = self.kb.query("What events are upcoming?")
        self.assertEqual(intent, "EVENT_INQUIRY")
        self.assertTrue(res["is_grounded"])
        self.assertIn("Intro to GenAI Workshop", res["answer"])
        self.assertEqual(res["source"], "Events")
        print("[TEST 5 PASSED] What events are upcoming? -> Source:", res["source"])

    def test_06_event_on_september_20(self):
        intent, _ = self.clf.classify("Which event is happening on September 20?")
        res = self.kb.query("Which event is happening on September 20?")
        self.assertEqual(intent, "EVENT_INQUIRY")
        self.assertTrue(res["is_grounded"])
        self.assertIn("Cloud Study Jam", res["answer"])
        self.assertEqual(res["source"], "Events → Cloud Study Jam")
        self.assertGreaterEqual(res["confidence"], 0.90)
        print("[TEST 6 PASSED] Which event is happening on September 20? -> Answer: Cloud Study Jam | Source:", res["source"])

    def test_07_how_can_i_join(self):
        intent, _ = self.clf.classify("How can I join the club?")
        res = self.kb.query("How can I join the club?")
        self.assertEqual(intent, "FAQ")
        self.assertTrue(res["is_grounded"])
        self.assertIn("Application Form", res["answer"])
        self.assertEqual(res["source"], "Recruitment")
        self.assertGreaterEqual(res["confidence"], 0.90)
        print("[TEST 7 PASSED] How can I join the club? -> Source:", res["source"])

    def test_08_who_is_president(self):
        intent, _ = self.clf.classify("Who is the president?")
        res = self.kb.query("Who is the president?")
        self.assertEqual(intent, "FAQ")
        self.assertTrue(res["is_grounded"])
        self.assertIn("Aditya Kumar", res["answer"])
        self.assertEqual(res["source"], "Contacts")
        print("[TEST 8 PASSED] Who is the president? -> Answer: Aditya Kumar | Source:", res["source"])

    def test_09_annual_budget_ungrounded(self):
        res = self.kb.query("What is the club's annual budget?")
        self.assertFalse(res["is_grounded"])
        self.assertIn("have no idea", res["answer"].lower())
        self.assertEqual(res["source"], "None")
        self.assertEqual(res["confidence"], 0.20)
        print("[TEST 9 PASSED] Annual budget (Ungrounded) -> Refusal: Yes ('I have no idea') | Conf:", res["confidence"])

    def test_10_programming_languages_ungrounded(self):
        res = self.kb.query("What programming languages does the AIML team use?")
        self.assertFalse(res["is_grounded"])
        self.assertIn("have no idea", res["answer"].lower())
        self.assertEqual(res["source"], "None")
        self.assertEqual(res["confidence"], 0.20)
        print("[TEST 10 PASSED] AIML languages (Ungrounded attribute) -> Refusal: Yes ('I have no idea') | Conf:", res["confidence"])

if __name__ == "__main__":
    unittest.main()
