import re
from typing import Dict, Any

def is_valid_email(email_str: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email_str.strip()))

class AgentEngine:
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

    def process_action(self, intent: str, user_message: str, session_state: Dict[str, Any], user_memory: Dict[str, Any] = None) -> Dict[str, Any]:
        msg = user_message.strip()
        msg_lower = msg.lower()
        current_action = session_state.get("action_type")
        user_memory = user_memory or {}

        if "feedback" in msg_lower or current_action == "Feedback":
            action_type = "Feedback"
        elif "status" in msg_lower or current_action == "Status Check":
            action_type = "Status Check"
        else:
            action_type = "Event Registration"

        # -------------------------------------------------------------
        # Action 1: Event Registration
        # -------------------------------------------------------------
        if action_type == "Event Registration":
            slots = session_state.get("slots", {})

            # Pre-fill from user memory if available and missing
            if "name" not in slots and user_memory.get("name"):
                slots["name"] = user_memory["name"]
            if "email" not in slots and user_memory.get("email"):
                slots["email"] = user_memory["email"]

            # Extract event title
            if "event" not in slots:
                if "genai" in msg_lower or "workshop" in msg_lower:
                    slots["event"] = "Intro to GenAI Workshop"
                elif "cloud" in msg_lower:
                    slots["event"] = "Cloud Study Jam"
                elif "hackfest" in msg_lower or "hackathon" in msg_lower:
                    slots["event"] = "HackFest 2025"
                elif "design" in msg_lower or "bootcamp" in msg_lower:
                    slots["event"] = "Design Thinking Bootcamp"
                elif "cyber" in msg_lower or "ctf" in msg_lower:
                    slots["event"] = "CyberCTF Challenge"

            # Slot 1: Name
            if "name" not in slots and session_state.get("prompting") == "name":
                name_match = re.search(r"(?:my name is|i am|name:?)\s+([a-zA-Z\s]+)", msg, re.I)
                extracted_name = name_match.group(1).strip() if name_match else msg
                slots["name"] = extracted_name.capitalize()
                user_memory["name"] = slots["name"]

            elif "name" not in slots:
                name_match = re.search(r"(?:my name is|i am|name:?)\s+([a-zA-Z\s]+)", msg, re.I)
                if name_match:
                    slots["name"] = name_match.group(1).strip().capitalize()
                    user_memory["name"] = slots["name"]

            # Slot 2: Email
            if "email" not in slots and session_state.get("prompting") == "email":
                if is_valid_email(msg):
                    slots["email"] = msg.strip()
                    user_memory["email"] = slots["email"]
                else:
                    session_state["action_type"] = "Event Registration"
                    session_state["slots"] = slots
                    session_state["prompting"] = "email"
                    return {
                        "answer": "⚠️ That doesn't look like a valid email address. Please enter a valid email (e.g. name@example.com):",
                        "action_complete": False,
                        "session_state": session_state,
                        "user_memory": user_memory
                    }

            # Slot 3: Academic Year
            if "year" not in slots and session_state.get("prompting") == "year":
                slots["year"] = msg.strip()

            # Step 1: Prompt Event
            if "event" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "event"
                return {
                    "answer": "Which event would you like to register for?\n\n• **Intro to GenAI Workshop** (Sept 15)\n• **Cloud Study Jam** (Sept 20)\n• **Design Thinking Bootcamp** (Sept 25)\n• **HackFest 2025** (Oct 10)\n• **CyberCTF Challenge** (Nov 5)",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # Step 2: Prompt Name
            if "name" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "name"
                return {
                    "answer": f"Got it! Registering for **{slots['event']}**. What is your full name?",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # Step 3: Prompt Email
            if "email" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "email"
                return {
                    "answer": f"Thanks {slots['name']}! What is your email address for sending the ticket?",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # Step 4: Prompt Year
            if "year" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "year"
                return {
                    "answer": "What is your academic year of study? (e.g. 1st Year, 2nd Year, 3rd Year)",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # All slots complete -> Execute Registration
            ticket_id = self.dm.add_registration(
                name=slots["name"],
                email=slots["email"],
                year=slots["year"],
                event_title=slots["event"]
            )

            # Store in user memory permanently
            user_memory["name"] = slots["name"]
            user_memory["email"] = slots["email"]

            return {
                "answer": f"🎉 **Registration Successful!**\n\n• **Ticket ID**: `{ticket_id}`\n• **Name**: {slots['name']}\n• **Event**: {slots['event']}\n• **Email**: {slots['email']}\n• **Year**: {slots['year']}\n\nYour registration has been saved to the database.",
                "action_complete": True,
                "session_state": {},
                "user_memory": user_memory
            }

        # -------------------------------------------------------------
        # Action 2: Feedback
        # -------------------------------------------------------------
        if action_type == "Feedback":
            slots = session_state.get("slots", {})

            if "email" not in slots and user_memory.get("email"):
                slots["email"] = user_memory["email"]

            if "email" not in slots and session_state.get("prompting") == "email":
                if is_valid_email(msg):
                    slots["email"] = msg.strip()
                    user_memory["email"] = slots["email"]
                else:
                    session_state["action_type"] = "Feedback"
                    session_state["slots"] = slots
                    session_state["prompting"] = "email"
                    return {
                        "answer": "⚠️ Please enter a valid email address (e.g. name@example.com):",
                        "action_complete": False,
                        "session_state": session_state,
                        "user_memory": user_memory
                    }

            if "message" not in slots and session_state.get("prompting") == "message":
                slots["message"] = msg

            if "email" not in slots:
                session_state["action_type"] = "Feedback"
                session_state["slots"] = slots
                session_state["prompting"] = "email"
                return {
                    "answer": "We welcome your feedback! Please provide your email address:",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            if "message" not in slots:
                session_state["action_type"] = "Feedback"
                session_state["slots"] = slots
                session_state["prompting"] = "message"
                return {
                    "answer": "Please enter your feedback message for the GDG On Campus team:",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            fb_id = self.dm.add_feedback(slots["email"], "General Feedback", slots["message"])
            user_memory["email"] = slots["email"]

            return {
                "answer": f"✅ **Feedback Submitted!**\n\n• **Reference ID**: `{fb_id}`\n• **Email**: {slots['email']}\n\nThank you for helping us improve GDG On Campus!",
                "action_complete": True,
                "session_state": {},
                "user_memory": user_memory
            }

        # -------------------------------------------------------------
        # Action 3: Status Check
        # -------------------------------------------------------------
        if action_type == "Status Check":
            app_status = self.dm.get_application_status(msg)
            if app_status:
                return {
                    "answer": f"📋 **Recruitment Application Status**:\n\n• **Applicant**: {app_status['name']}\n• **Application ID**: `{app_status['id']}`\n• **Current Stage**: **{app_status['stage']}**",
                    "action_complete": True,
                    "session_state": {},
                    "user_memory": user_memory
                }
            return {
                "answer": "Please provide your candidate name (e.g. *Aarav Sharma*) or Application ID (e.g. *APP-1001*) to check your status:",
                "action_complete": False,
                "session_state": {"action_type": "Status Check"},
                "user_memory": user_memory
            }

        return {"answer": "Action processed.", "action_complete": True, "session_state": {}, "user_memory": user_memory}
