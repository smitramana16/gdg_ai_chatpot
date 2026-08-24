import os
import re
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.data_manager import DataManager
from app.intent_classifier import IntentClassifier
from app.kb_engine import KnowledgeEngine
from app.agent_engine import AgentEngine

app = FastAPI(title="GDG Club FAQ Assistant & Dashboard", version="3.0.0")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

data_mgr = DataManager()
intent_clf = IntentClassifier()
kb_eng = KnowledgeEngine()
agent_eng = AgentEngine(data_mgr)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []
    session_state: Optional[Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>GDG Club FAQ Assistant API</h1>"

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message.strip()
    session_state = req.session_state or {}
    history = req.history or []

    user_memory = session_state.get("user_memory", {})
    action_state = session_state.get("action_state", {})

    # Legacy flat fallback compatibility
    if not user_memory and "name" in session_state.get("slots", {}):
        user_memory["name"] = session_state["slots"]["name"]
    if not action_state and session_state.get("action_type"):
        action_state = session_state

    # 1. ALWAYS Classify the incoming user message FIRST!
    intent, confidence = intent_clf.classify(user_msg)

    # 2. Check for Cancellation Intent
    if intent == "CANCEL":
        return JSONResponse({
            "answer": "Action cancelled. How else can I assist you with GDG On Campus?",
            "intent": "CANCEL",
            "confidence": 99,
            "source": "System",
            "is_action": False,
            "session_state": {
                "user_memory": user_memory,
                "action_state": {}
            }
        })

    # 3. Check for Session Memory Queries ("Do you remember my name?", "What is my email?")
    if intent == "MEMORY_QUERY":
        msg_lower = user_msg.lower()
        if "email" in msg_lower:
            if user_memory.get("email"):
                ans = f"Yes, I remember your email. Your email is **{user_memory['email']}**."
            else:
                ans = "I don't have your email address stored in this conversation."
        elif any(w in msg_lower for w in ["detail", "information", "about me"]):
            details = []
            if user_memory.get("name"): details.append(f"Name: **{user_memory['name']}**")
            if user_memory.get("email"): details.append(f"Email: **{user_memory['email']}**")
            if details:
                ans = "Here are the details I remember about you from this session:\n\n• " + "\n• ".join(details)
            else:
                ans = "I don't have any personal details stored about you in this conversation yet."
        else:
            if user_memory.get("name"):
                ans = f"Yes, I remember your name! Your name is **{user_memory['name']}**."
            else:
                ans = "I don't have your name stored in this conversation."

        data_mgr.record_chat(
            intent="MEMORY_QUERY",
            confidence=0.98,
            is_success=True,
            is_action=False,
            user_query=user_msg
        )

        return JSONResponse({
            "answer": ans,
            "intent": "MEMORY_QUERY",
            "confidence": 98,
            "source": "Session Memory",
            "is_action": False,
            "session_state": {
                "user_memory": user_memory,
                "action_state": action_state
            }
        })

    # 4. Handle Topic Switching (User asks FAQ / Event query while action was pending)
    current_action = action_state.get("action_type")
    if current_action and intent in ["FAQ", "EVENT_INQUIRY", "GREETING"]:
        action_state = {} # Topic switched -> clear/pause pending action

    # 5. Route to Action Engine ONLY if explicitly requested or answering pending action
    if intent == "ACTION_REQUEST" or (action_state.get("action_type") and intent not in ["FAQ", "EVENT_INQUIRY"]):
        action_res = agent_eng.process_action(intent, user_msg, action_state, user_memory)
        is_completed = action_res.get("action_complete", False)
        new_user_memory = action_res.get("user_memory", user_memory)
        new_action_state = {} if is_completed else action_res.get("session_state", {})

        data_mgr.record_chat(
            intent="ACTION_REQUEST",
            confidence=confidence,
            is_success=True,
            is_action=is_completed,
            user_query=user_msg
        )

        return JSONResponse({
            "answer": action_res.get("answer"),
            "intent": "ACTION_REQUEST",
            "confidence": int(confidence * 100),
            "source": "Agentic Workflow Engine",
            "is_action": True,
            "session_state": {
                "user_memory": new_user_memory,
                "action_state": new_action_state
            }
        })

    # 6. Route Grounded Q&A
    kb_res = kb_eng.query(user_msg, history)
    is_success = kb_res.get("is_grounded", False)
    final_confidence = kb_res.get("confidence", confidence)

    # Store self-introductions in user_memory
    if user_msg.lower().startswith("my name is") or user_msg.lower().startswith("i am "):
        name_match = re.search(r"(?:my name is|i am)\s+([a-zA-Z\s]+)", user_msg, re.I)
        if name_match:
            extracted = name_match.group(1).strip().capitalize()
            if extracted.lower() not in ["asking", "wondering", "looking"]:
                user_memory["name"] = extracted

    if intent == "GREETING":
        final_intent = "GREETING"
    elif not is_success or "i have no idea" in kb_res.get("answer", "").lower():
        final_intent = "UNKNOWN"
    elif intent in ["FAQ", "EVENT_INQUIRY"]:
        final_intent = intent
    else:
        final_intent = "FAQ"

    data_mgr.record_chat(
        intent=final_intent,
        confidence=final_confidence,
        is_success=is_success,
        is_action=False,
        user_query=user_msg
    )

    return JSONResponse({
        "answer": kb_res.get("answer"),
        "intent": final_intent,
        "confidence": int(final_confidence * 100),
        "source": kb_res.get("source"),
        "is_action": False,
        "subject": kb_res.get("subject"),
        "session_state": {
            "user_memory": user_memory,
            "action_state": {}
        }
    })

@app.get("/api/dashboard/stats")
async def get_stats():
    storage = data_mgr.load_storage()
    return storage.get("stats", {})

@app.get("/api/dashboard/actions")
async def get_actions():
    storage = data_mgr.load_storage()
    return {
        "registrations": storage.get("registrations", []),
        "feedback_entries": storage.get("feedback_entries", [])
    }

@app.get("/api/dashboard/unanswered")
async def get_unanswered():
    storage = data_mgr.load_storage()
    return storage.get("unanswered_log", [])

@app.get("/api/knowledge")
async def get_knowledge():
    return kb_eng.kb_data
