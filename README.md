# 🤖 GDG On Campus — AI Assistant & Admin Dashboard

An AI-powered conversational chatbot and real-time analytics dashboard built for **GDG On Campus**. Grounded strictly in official club information, it provides accurate Q&A, retains multi-turn context, classifies user intents, computes confidence scores, cites sources, executes agentic workflows (Event Registration, Feedback Submission, Status Checking), and provides an interactive admin dashboard.

---

## 🌟 Key Features

### 1. 🤖 Grounded FAQ Chatbot
- **Strict Grounding**: Answers questions using *only* official GDG On Campus data (Introduction, Teams, Events, Recruitment, Rules, Contacts, Achievements).
- **Hallucination Prevention**: Explicitly rejects out-of-scope questions with `"I have no idea about that."` (20% confidence, `UNKNOWN` intent).
- **Dynamic Source Citations**: Shows exact data sources (e.g. `Source: Teams → AIML`, `Source: Events → Intro to GenAI Workshop`).
- **Dynamic Confidence Scoring**: Evaluates exact and semantic match ratios (e.g. 98% exact, 75–88% fuzzy, <45% fallback).
- **Intent Classification**: Categorizes user intent into `GREETING`, `FAQ`, `EVENT_INQUIRY`, `ACTION_REQUEST`, `UNKNOWN`, `MEMORY_QUERY`, or `CANCEL`.

### 2. ⚡ Agentic Workflows
- **Action 1: Event Registration**: Conversational step-by-step slot-filling (Name → Email → Year → Event Choice) → generates ticket ID (e.g. `REG-A4F19B`). Includes strict email syntax validation.
- **Action 2: Feedback & Query Submission**: Collects email and feedback message → generates reference ID (e.g. `FB-89C21A`).
- **Action 3: Recruitment Application Status**: Looks up candidate stage (e.g. `APP-1001` → `Interview Scheduled`).
- **Data Persistence**: All action records survive server restarts in `data/storage.json`.

### 3. 🧠 Smart Multi-Turn Memory
- **Context Resolution**: Resolves follow-ups like *"Who leads AIML?"* → *"What about Web Dev?"* (resolves *"Who leads Web Dev?"*).
- **Session User Memory**: Separates persistent identity (`user_memory`) from task workflow slots (`action_state`). Responds to memory queries like *"Do you remember my name?"* or *"What is my email?"*.
- **Workflow Priority**: Users can pause an active registration to ask an FAQ question or cancel the action without hijacking the chat flow.

### 4. 📊 Interactive Admin Dashboard
- **KPI Metrics**: Total Chats, Grounded Answers, Actions Executed, Unanswered Queries Count.
- **Intent Distribution Chart**: Dynamic Donut Chart (Chart.js) breaking down user query intents.
- **Actions Log Table**: Live table showing all event registrations and feedback submissions.
- **Unanswered Queries Queue**: Admin review table for logged low-confidence questions.
- **Knowledge Base Browser**: Interactive tab displaying all 7 official knowledge categories.

---

## 📁 Project Structure

```text
my first ml project/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI REST API & static routing
│   ├── kb_engine.py             # Grounded RAG matcher, date parser, hallucination guardrail
│   ├── agent_engine.py          # Conversational agentic workflow state machine
│   ├── intent_classifier.py     # Intent classification engine
│   └── data_manager.py          # Persistent storage & stats manager
├── data/
│   ├── club_knowledge.json      # Official GDG On Campus ground truth data (7 categories)
│   └── storage.json             # Runtime database (registrations, feedback, unanswered queries)
├── static/
│   ├── index.html               # Multi-tab Web Interface (Chatbot, Dashboard, Knowledge Base)
│   ├── style.css                # Dark mode styling, glassmorphism, GDG neon accents
│   └── app.js                   # Asynchronous API client, typing animations, Chart.js logic
├── PRD.md                       # Product Requirements Document
├── run.py                       # Server entry point
├── test_10_required_questions.py# Test suite for 10 core questions
└── test_action_workflow_memory.py # Test suite for memory & workflow state isolation
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Installed packages: `fastapi`, `uvicorn`, `pydantic`

### Installation & Execution

1. **Clone Repository**:
   ```bash
   git clone https://github.com/smitramana16/gdg_ai_chatpot.git
   cd gdg_ai_chatpot
   ```

2. **Start Server**:
   ```bash
   python run.py
   ```

3. **Open Web Interface**:
   Navigate to **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Running Automated Tests

To run the full verification test suite:

```bash
python test_10_required_questions.py
python test_action_workflow_memory.py
```

---

## 📄 License
This project is open-source under the MIT License.
