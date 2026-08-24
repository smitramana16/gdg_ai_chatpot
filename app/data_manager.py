import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STORAGE_FILE = os.path.join(DATA_DIR, "storage.json")

class DataManager:
    def __init__(self, storage_path: str = STORAGE_FILE):
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.storage_path):
            default_data = {
                "stats": {
                    "total_chats": 0,
                    "successful_queries": 0,
                    "unanswered_queries": 0,
                    "actions_completed": 0,
                    "intent_counts": {
                        "FAQ Inquiry": 0,
                        "Event Query": 0,
                        "Action: Event Registration": 0,
                        "Action: Feedback": 0,
                        "Action: Status Check": 0,
                        "Greeting": 0,
                        "Out of Scope": 0
                    }
                },
                "registrations": [],
                "feedback_entries": [],
                "unanswered_log": [],
                "applications": []
            }
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=2)

    def load_storage(self) -> Dict[str, Any]:
        self._ensure_storage()
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_storage(self, data: Dict[str, Any]):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def record_chat(self, intent: str, confidence: float, is_success: bool, is_action: bool, user_query: str = ""):
        storage = self.load_storage()
        stats = storage.get("stats", {})
        stats["total_chats"] = stats.get("total_chats", 0) + 1

        if is_success:
            stats["successful_queries"] = stats.get("successful_queries", 0) + 1
        else:
            stats["unanswered_queries"] = stats.get("unanswered_queries", 0) + 1
            # Log unanswered query
            if user_query:
                unanswered = storage.get("unanswered_log", [])
                unanswered.append({
                    "id": str(uuid.uuid4())[:8],
                    "query": user_query,
                    "confidence": round(confidence * 100, 1),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                storage["unanswered_log"] = unanswered

        if is_action:
            stats["actions_completed"] = stats.get("actions_completed", 0) + 1

        intents = stats.get("intent_counts", {})
        intents[intent] = intents.get(intent, 0) + 1
        stats["intent_counts"] = intents
        storage["stats"] = stats
        self.save_storage(storage)

    def add_registration(self, name: str, email: str, year: str, event_title: str) -> str:
        storage = self.load_storage()
        ticket_id = f"REG-{str(uuid.uuid4())[:6].upper()}"
        reg_entry = {
            "ticket_id": ticket_id,
            "name": name,
            "email": email,
            "year": year,
            "event_title": event_title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        registrations = storage.get("registrations", [])
        registrations.append(reg_entry)
        storage["registrations"] = registrations
        self.save_storage(storage)
        return ticket_id

    def add_feedback(self, email: str, category: str, message: str) -> str:
        storage = self.load_storage()
        fb_id = f"FB-{str(uuid.uuid4())[:6].upper()}"
        entry = {
            "id": fb_id,
            "email": email,
            "category": category,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        feedbacks = storage.get("feedback_entries", [])
        feedbacks.append(entry)
        storage["feedback_entries"] = feedbacks
        self.save_storage(storage)
        return fb_id

    def get_application_status(self, query: str) -> Dict[str, Any]:
        storage = self.load_storage()
        apps = storage.get("applications", [])
        query_lower = query.lower().strip()
        for app in apps:
            if (app.get("id", "").lower() in query_lower or 
                app.get("email", "").lower() in query_lower or 
                app.get("name", "").lower() in query_lower):
                return app
        return None
