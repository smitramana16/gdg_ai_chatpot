import re
from typing import Dict, Any
from app.data_manager import DataManager

def is_valid_email(email_str: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email_str.strip()))

UPCOMING_EVENTS = [
    "Intro to GenAI Workshop",
    "Cloud Study Jam",
    "Design Thinking Bootcamp",
    "HackFest 2025",
    "CyberCTF Challenge"
]

COMPLETED_EVENTS = [
    "Flutter Forward"
]

class AgentEngine:
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

    def match_event_title(self, text: str) -> str:
        t = text.lower()
        if "genai" in t or "intro to genai" in t:
            return "Intro to GenAI Workshop"
        if "cloud study" in t or "cloud jam" in t or "study jam" in t or ("cloud" in t and "jam" in t):
            return "Cloud Study Jam"
        if "design thinking" in t or "bootcamp" in t or ("design" in t and "bootcamp" in t):
            return "Design Thinking Bootcamp"
        if "hackfest" in t or "hackfest 2025" in t or "hackathon" in t:
            return "HackFest 2025"
        if "cyberctf" in t or "ctf" in t or "cyberctf challenge" in t:
            return "CyberCTF Challenge"
        return None

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

            # 1. Detect requested event if not yet stored
            if "event" not in slots:
                matched_ev = self.match_event_title(msg)
                
                if matched_ev:
                    slots["event"] = matched_ev
                elif "flutter" in msg_lower or "flutter forward" in msg_lower:
                    options = [f"Register for {ev}" for ev in UPCOMING_EVENTS]
                    return {
                        "answer": "Flutter Forward is a completed event. You can only register for upcoming events.\n\nWould you like to register for any of these upcoming events?",
                        "action_complete": True,
                        "session_state": {},
                        "user_memory": user_memory,
                        "options": options
                    }
                elif "register" in msg_lower or "sign up" in msg_lower or "enroll" in msg_lower:
                    # User asked to register for an event, check if they specified an unknown event name (e.g., "AI Summit")
                    match = re.search(r"register\s+(?:me\s+)?(?:for\s+)?(?:the\s+)?(.+)", msg, re.I)
                    if match:
                        requested_name = match.group(1).strip()
                        # If requested_name doesn't match any known upcoming event
                        matched_ev = self.match_event_title(requested_name)
                        if matched_ev:
                            slots["event"] = matched_ev
                        else:
                            options = [f"Register for {ev}" for ev in UPCOMING_EVENTS]
                            ev_list = "\n".join([f"• **{ev}**" for ev in UPCOMING_EVENTS])
                            return {
                                "answer": f"I don't see that event in the available club events.\n\nAvailable upcoming events:\n{ev_list}\n\nWould you like to register for any of these events?",
                                "action_complete": True,
                                "session_state": {},
                                "user_memory": user_memory,
                                "options": options
                            }

            # 2. Extract Name/Email inputs based on current prompting step
            prompting = session_state.get("prompting")

            # Slot 1: Name input
            if "event" in slots and "name" not in slots and prompting == "name":
                name_match = re.search(r"(?:my name is|i am|name:?)\s+([a-zA-Z\s]+)", msg, re.I)
                extracted_name = name_match.group(1).strip() if name_match else msg
                slots["name"] = extracted_name.capitalize()
                user_memory["name"] = slots["name"]

            # Slot 2: Email input
            if "event" in slots and "name" in slots and "email" not in slots and prompting == "email":
                if is_valid_email(msg):
                    slots["email"] = msg.strip()
                    user_memory["email"] = slots["email"]
                else:
                    session_state["action_type"] = "Event Registration"
                    session_state["slots"] = slots
                    session_state["prompting"] = "email"
                    return {
                        "answer": "Please provide a valid email address.",
                        "action_complete": False,
                        "session_state": session_state,
                        "user_memory": user_memory
                    }

            # ---------------------------------------------------------
            # Step-by-Step Prompting Flow
            # ---------------------------------------------------------

            # Step 1: Prompt for Event choice if still missing
            if "event" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "event"
                options = [f"Register for {ev}" for ev in UPCOMING_EVENTS]
                return {
                    "answer": "Which event would you like to register for?\n\n• **Intro to GenAI Workshop** (Sept 15)\n• **Cloud Study Jam** (Sept 20)\n• **Design Thinking Bootcamp** (Sept 25)\n• **HackFest 2025** (Oct 10)\n• **CyberCTF Challenge** (Nov 5)",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory,
                    "options": options
                }

            # Step 2: Prompt for Name
            if "name" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "name"
                return {
                    "answer": f"Sure! I'll help you register for the {slots['event']}. What is your name?",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # Step 3: Prompt for Email
            if "email" not in slots:
                session_state["action_type"] = "Event Registration"
                session_state["slots"] = slots
                session_state["prompting"] = "email"
                return {
                    "answer": f"Thanks, {slots['name']}. What is your email address?",
                    "action_complete": False,
                    "session_state": session_state,
                    "user_memory": user_memory
                }

            # Step 4: All slots complete -> Execute & Persist Registration
            ticket_id = self.dm.add_registration(
                name=slots["name"],
                email=slots["email"],
                year=slots.get("year", "Student"),
                event_title=slots["event"]
            )

            user_memory["name"] = slots["name"]
            user_memory["email"] = slots["email"]

            return {
                "answer": f"Registration successful!\n\nEvent: {slots['event']}\nName: {slots['name']}\nEmail: {slots['email']}",
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
                        "answer": "Please provide a valid email address.",
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
