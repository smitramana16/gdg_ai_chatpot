import re
from typing import Tuple

class IntentClassifier:
    def __init__(self):
        self.greetings = [
            r"^\s*hi\b", r"^\s*hello\b", r"^\s*hey\b", r"^\s*good\s*(morning|afternoon|evening)\b",
            r"^\s*greetings\b", r"^\s*who\s+are\s+you\b", r"^\s*what\s+can\s+you\s+do\b"
        ]

        self.cancellations = [
            r"^\s*cancel\b", r"^\s*cancel\s+this\b", r"^\s*stop\b", r"^\s*abort\b", r"^\s*nevermind\b", r"^\s*exit\b"
        ]

        self.memory_queries = [
            r"remember\s+my\s+name", r"what\s+is\s+my\s+name", r"what's\s+my\s+name", r"do\s+you\s+know\s+my\s+name",
            r"my\s+name\b", r"remember\s+my\s+email", r"what\s+is\s+my\s+email", r"what's\s+my\s+email",
            r"remember\s+my\s+details", r"details\s+do\s+you\s+remember", r"what\s+name\s+did\s+i\s+give",
            r"still\s+remember\s+my"
        ]

        self.action_keywords = [
            r"\bregister\b", r"\bregester\b", r"sign\s*up", r"join\s+event", r"enroll", r"\bfeedback\b",
            r"complain", r"suggestion", r"\bstatus\b", r"check\s*status", r"application\s*status"
        ]

        self.event_keywords = [
            r"event", r"workshop", r"hackathon", r"bootcamp", r"hackfest", r"genai",
            r"cloud\s+study", r"flutter", r"cyberctf", r"upcoming", r"completed", r"schedule",
            r"september", r"sept\b", r"october", r"oct\b", r"november", r"nov\b", r"august", r"aug\b",
            r"happening", r"scheduled"
        ]

        self.faq_keywords = [
            r"team", r"lead", r"leed", r"head", r"leader", r"who\s+leads", r"member",
            r"recruitment", r"apply", r"join", r"eligibility", r"eligible", r"rule", r"active",
            r"alumni", r"contact", r"email", r"president", r"vp", r"tech\s+head", r"achievement",
            r"award", r"star", r"github", r"devfest", r"gdg", r"about", r"intro", r"founded",
            r"started", r"begin", r"start", r"who\s+is", r"process"
        ]

    def classify(self, text: str) -> Tuple[str, float]:
        t = text.lower().strip()

        # 1. CANCEL
        if any(re.search(pat, t) for pat in self.cancellations):
            return "CANCEL", 0.99

        # 2. MEMORY_QUERY (Distinguish from "remember to register me...")
        if any(re.search(pat, t) for pat in self.memory_queries):
            if not any(re.search(pat, t) for pat in self.action_keywords):
                return "MEMORY_QUERY", 0.98

        # 3. GREETING
        if any(re.search(pat, t) for pat in self.greetings):
            return "GREETING", 0.99

        # 4. ACTION_REQUEST
        if any(re.search(pat, t) for pat in self.action_keywords):
            return "ACTION_REQUEST", 0.95

        # 5. EVENT_INQUIRY
        if any(re.search(pat, t) for pat in self.event_keywords):
            return "EVENT_INQUIRY", 0.92

        # 6. FAQ
        if any(re.search(pat, t) for pat in self.faq_keywords):
            return "FAQ", 0.88

        if any(w in t for w in ["what", "who", "where", "when", "how"]):
            return "FAQ", 0.60

        return "UNKNOWN", 0.20
