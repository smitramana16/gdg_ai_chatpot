import json
import os
import re
from typing import Dict, Any, List, Tuple

KB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "club_knowledge.json")

class KnowledgeEngine:
    def __init__(self, kb_path: str = KB_FILE):
        self.kb_path = kb_path
        self.kb_data = self._load_kb()

    def _load_kb(self) -> Dict[str, Any]:
        if not os.path.exists(self.kb_path):
            return {}
        with open(self.kb_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def normalize_text(self, text: str) -> str:
        t = text.lower().strip()
        t = re.sub(r"\bleed\b", "lead", t)
        t = re.sub(r"\bleader\b", "lead", t)
        t = re.sub(r"\bhead\b", "lead", t)
        t = re.sub(r"\bin-charge\b", "lead", t)
        t = re.sub(r"\bwhos\b", "who is", t)
        t = re.sub(r"\bregester\b", "register", t)
        return t

    def query(self, user_query: str, session_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        raw_query = user_query.strip()
        norm_query = self.normalize_text(raw_query)

        # 1. Check for Ungrounded Requested Attributes (Hallucination Guardrail)
        ungrounded_attributes = [
            "budget", "annual budget", "programming language", "programming languages", "languages",
            "tech stack", "salary", "sponsor", "sponsors", "location", "venue", "phone number",
            "finance head", "treasurer", "address"
        ]
        if any(attr in norm_query for attr in ungrounded_attributes):
            return {
                "answer": "I have no idea about that. I can only answer questions grounded in our official GDG On Campus club information.",
                "source": "None",
                "confidence": 0.20,
                "is_grounded": False,
                "subject": None
            }

        # 2. Greetings
        if norm_query in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]:
            return {
                "answer": "Hello! I am the GDG On Campus Assistant. How can I help you today?",
                "source": "Greeting",
                "confidence": 0.99,
                "is_grounded": True,
                "subject": None
            }

        # 3. Name Introductions ("my name is...")
        if norm_query.startswith("my name is") or norm_query.startswith("i am "):
            name_part = re.sub(r"^(my name is|i am)\s*", "", raw_query, flags=re.I).strip()
            if name_part and name_part.lower() not in ["asking", "wondering", "looking"]:
                return {
                    "answer": f"Nice to meet you, **{name_part.capitalize()}**! 👋 How can I help you with GDG On Campus today? You can ask about our teams, events, recruitment, or register for an event!",
                    "source": "User Intro",
                    "confidence": 0.98,
                    "is_grounded": True,
                    "subject": None
                }

        # 4. Context Resolution
        resolved_query, context_subject = self._resolve_context(norm_query, session_history)

        vague_phrases = ["tell me about it", "what about it", "explain it", "details"]
        if norm_query in vague_phrases and not context_subject:
            return {
                "answer": "Could you please specify what team, event, or rule you'd like to know about?",
                "source": "System Guidance",
                "confidence": 0.50,
                "is_grounded": True,
                "subject": None
            }

        q = resolved_query.lower()
        results = []

        # -------------------------------------------------------------
        # Category: Introduction
        # -------------------------------------------------------------
        if any(w in q for w in ["founded", "found", "start", "started", "begin", "began", "established", "created", "history", "about gdg", "introduction", "what is gdg", "overview"]):
            intro = self.kb_data.get("Introduction", "")
            if any(w in q for w in ["founded", "found", "start", "started", "begin", "began", "established", "created", "year"]):
                answer_str = "GDG On Campus was **founded in 2022**. It is a community of 150+ tech enthusiasts that organizes workshops, hackathons, and speaker sessions."
            else:
                answer_str = f"**GDG On Campus**:\n{intro}"
            results.append({
                "answer": answer_str,
                "source": "Club Introduction",
                "confidence": 0.96,
                "subject": "Introduction"
            })

        # -------------------------------------------------------------
        # Category: Teams & Leads
        # -------------------------------------------------------------
        teams = self.kb_data.get("Teams", [])
        for team in teams:
            t_name = team["name"].lower()
            t_lead = team["lead"]

            if t_name in q or (context_subject and context_subject.lower() in t_name):
                if any(w in q for w in ["lead", "who", "run", "manager", "head"]):
                    results.append({
                        "answer": f"The lead for **{team['name']}** is **{t_lead}**.",
                        "source": f"Teams → {team['name']}",
                        "confidence": 0.98 if t_name in norm_query else 0.88,
                        "subject": f"Team:{team['name']}"
                    })
                else:
                    results.append({
                        "answer": f"**{team['name']}** (Lead: {t_lead})",
                        "source": f"Teams → {team['name']}",
                        "confidence": 0.92,
                        "subject": f"Team:{team['name']}"
                    })

        if "team" in q and ("available" in q or "list" in q or "what" in q or "all" in q or "how many" in q or "six" in q):
            teams_str = "\n".join([f"• **{t['name']}** (Lead: {t['lead']})" for t in teams])
            results.append({
                "answer": f"The available teams in GDG On Campus are:\n\n{teams_str}",
                "source": "Teams",
                "confidence": 0.98,
                "subject": "Teams"
            })

        # -------------------------------------------------------------
        # Category: Events & Date Semantic Matcher
        # -------------------------------------------------------------
        events = self.kb_data.get("Events", [])
        
        date_map = {
            "september 20": "Cloud Study Jam",
            "sept 20": "Cloud Study Jam",
            "20th": "Cloud Study Jam",
            "september 15": "Intro to GenAI Workshop",
            "sept 15": "Intro to GenAI Workshop",
            "15th": "Intro to GenAI Workshop",
            "september 25": "Design Thinking Bootcamp",
            "sept 25": "Design Thinking Bootcamp",
            "25th": "Design Thinking Bootcamp",
            "october 10": "HackFest 2025",
            "oct 10": "HackFest 2025",
            "10th": "HackFest 2025",
            "november 5": "CyberCTF Challenge",
            "nov 5": "CyberCTF Challenge",
            "5th": "CyberCTF Challenge",
            "august 30": "Flutter Forward",
            "aug 30": "Flutter Forward",
            "30th": "Flutter Forward"
        }

        matched_event_from_date = None
        for d_key, ev_name in date_map.items():
            if d_key in q:
                matched_event_from_date = ev_name
                break

        for ev in events:
            ev_title = ev["title"].lower()
            title_keywords = [w for w in ev_title.split() if w not in ["intro", "to", "the", "challenge", "bootcamp", "jam"]]
            
            is_date_match = (matched_event_from_date and matched_event_from_date.lower() in ev_title)
            is_title_match = ev_title in q or any(kw in q for kw in title_keywords if len(kw) > 3)
            is_context_match = context_subject and context_subject.lower() in ev_title

            if is_date_match or is_title_match or is_context_match:
                results.append({
                    "answer": f"**{ev['title']}**\n• **Date**: {ev['date']}\n• **Status**: {ev['status']}",
                    "source": f"Events → {ev['title']}",
                    "confidence": 0.96 if (is_date_match or ev_title in norm_query) else 0.85,
                    "subject": f"Event:{ev['title']}"
                })

        if ("event" in q or "workshop" in q or "hackathon" in q) and ("upcoming" in q or "all" in q or "list" in q or "what" in q or "schedule" in q):
            upcoming_events = [ev for ev in events if ev.get("status") == "Upcoming"]
            ev_str = "\n".join([f"• **{ev['title']}** — {ev['date']}" for ev in upcoming_events])
            options = [f"Register for {ev['title']}" for ev in upcoming_events]
            results.append({
                "answer": f"Upcoming GDG On Campus Events:\n\n{ev_str}\n\nWould you like to register for any of these events?",
                "source": "Events",
                "confidence": 0.97,
                "subject": "Events",
                "options": options
            })

        # -------------------------------------------------------------
        # Category: Recruitment
        # -------------------------------------------------------------
        if any(w in q for w in ["recruitment", "join", "apply", "application", "eligibility", "eligible", "process", "window", "get in", "how to join"]):
            rec = self.kb_data.get("Recruitment", {})
            results.append({
                "answer": f"**GDG Recruitment Guidelines**:\n• **Recruitment Window**: {rec.get('window')}\n• **Eligibility**: {rec.get('eligibility')}\n• **Process Stages**: {rec.get('process')}",
                "source": "Recruitment",
                "confidence": 0.96,
                "subject": "Recruitment"
            })

        # -------------------------------------------------------------
        # Category: Contacts
        # -------------------------------------------------------------
        contacts = self.kb_data.get("Contacts", [])
        if any(w in q for w in ["contact", "email", "president", "vp", "tech head", "reach"]):
            for c in contacts:
                role_name = c.get("role", "").lower()
                if role_name in q or (("president" in q or "head of club" in q) and role_name == "president"):
                    email_str = f" ({c['email']})" if "email" in c else ""
                    results.append({
                        "answer": f"The GDG On Campus **{c['role']}** is **{c.get('name', 'N/A')}**{email_str}.",
                        "source": "Contacts",
                        "confidence": 0.97,
                        "subject": "Contacts"
                    })

            if not results or not any(r["source"] == "Contacts" for r in results):
                c_str = []
                for c in contacts:
                    val = f"• **{c['role']}**"
                    if "name" in c: val += f": {c['name']}"
                    if "email" in c: val += f" ({c['email']})"
                    c_str.append(val)
                results.append({
                    "answer": f"**GDG On Campus Key Contacts**:\n" + "\n".join(c_str),
                    "source": "Contacts",
                    "confidence": 0.96,
                    "subject": "Contacts"
                })

        # -------------------------------------------------------------
        # Category: Rules
        # -------------------------------------------------------------
        if any(w in q for w in ["rule", "active", "alumni", "switch", "contribution", "policy"]):
            rules = self.kb_data.get("Rules", [])
            rules_str = "\n".join([f"• {r}" for r in rules])
            results.append({
                "answer": f"**GDG On Campus Rules**:\n{rules_str}",
                "source": "Rules",
                "confidence": 0.96,
                "subject": "Rules"
            })

        # -------------------------------------------------------------
        # Category: Achievements
        # -------------------------------------------------------------
        if any(w in q for w in ["achievement", "award", "star", "github", "devfest"]):
            ach = self.kb_data.get("Achievements", [])
            ach_str = "\n".join([f"• {a}" for a in ach])
            results.append({
                "answer": f"**GDG On Campus Achievements**:\n{ach_str}",
                "source": "Achievements",
                "confidence": 0.95,
                "subject": "Achievements"
            })

        # Pick best match if confidence >= 0.45
        if results:
            best = max(results, key=lambda x: x["confidence"])
            if best["confidence"] >= 0.45:
                return {
                    "answer": best["answer"],
                    "source": best["source"],
                    "confidence": best["confidence"],
                    "is_grounded": True,
                    "subject": best["subject"],
                    "options": best.get("options", [])
                }

        # Strict Fallback
        return {
            "answer": "I have no idea about that. I can only answer questions grounded in our official GDG On Campus club information.",
            "source": "None",
            "confidence": 0.20,
            "is_grounded": False,
            "subject": None
        }

    def _resolve_context(self, norm_query: str, history: List[Dict[str, str]]) -> Tuple[str, str]:
        if not history:
            return norm_query, None

        context_triggers = ["it", "that", "this team", "this event", "who leads it", "what about", "how about", "when is it"]
        has_trigger = any(re.search(r"\b" + re.escape(tr) + r"\b", norm_query) for tr in context_triggers) or norm_query.startswith("what about ") or norm_query.startswith("how about ")

        if not has_trigger:
            return norm_query, None

        last_subject = None
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("subject"):
                subj = msg.get("subject", "")
                if subj.startswith("Team:"):
                    last_subject = subj.replace("Team:", "")
                elif subj.startswith("Event:"):
                    last_subject = subj.replace("Event:", "")
                else:
                    last_subject = subj
                break

        if norm_query.startswith("what about ") or norm_query.startswith("how about "):
            target = norm_query.replace("what about ", "").replace("how about ", "").strip("? ")
            if any(t in target for t in ["aiml", "web", "app", "cloud", "cyber", "design"]):
                return f"who leads {target}", target

        if last_subject:
            return f"{norm_query} regarding {last_subject}", last_subject

        return norm_query, None
