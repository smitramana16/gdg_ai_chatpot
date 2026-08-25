let chatHistory = [];
let sessionState = {};
let intentChartInstance = null;
let groundingChartInstance = null;

const API_BASE = (window.location.protocol === "file:" || !window.location.host)
  ? "http://127.0.0.1:8000"
  : "";

document.addEventListener("DOMContentLoaded", () => {
  lucide.createIcons();
  setupTabs();
  setupChatForm();
  loadKnowledgeBase();
  loadDashboardData();
});

function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetTab = document.getElementById(btn.dataset.tab);
      if (targetTab) targetTab.classList.add("active");

      if (btn.dataset.tab === "dashboard-tab") {
        loadDashboardData();
      }
    });
  });
}

function setupChatForm() {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("user-input");
  const clearBtn = document.getElementById("clear-chat");

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    appendMessage("user", text);
    input.value = "";
    sendMessageToBackend(text);
  });

  clearBtn.addEventListener("click", () => {
    chatHistory = [];
    sessionState = {};
    const chatContainer = document.getElementById("chat-messages");
    chatContainer.innerHTML = `
      <div class="message bot-message fade-in">
        <div class="avatar">🤖</div>
        <div class="message-content">
          <p>New chat session started! Memory cleared. How can I help you?</p>
        </div>
      </div>
    `;
    resetInspector();
  });
}

function sendQuickMessage(msg) {
  appendMessage("user", msg);
  sendMessageToBackend(msg);
}

function appendMessage(role, text, meta = {}) {
  const chatContainer = document.getElementById("chat-messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role === "user" ? "user-message" : "bot-message"} fade-in`;

  let contentHtml = `<p>${formatText(text)}</p>`;

  if (role === "bot" && meta.options && meta.options.length > 0) {
    let optionsHtml = '<div class="message-options-grid">';
    meta.options.forEach((opt) => {
      const cleanOpt = opt.replace(/'/g, "\\'");
      optionsHtml += `<button class="option-btn" onclick="sendQuickMessage('${cleanOpt}')">🎟️ ${opt}</button>`;
    });
    optionsHtml += '</div>';
    contentHtml += optionsHtml;
  }

  if (role === "bot" && (meta.intent || meta.confidence !== undefined)) {
    const confClass = meta.confidence >= 70 ? "high" : "low";
    contentHtml += `
      <div class="meta-row">
        ${meta.intent ? `<span class="badge intent-badge">${meta.intent}</span>` : ""}
        ${meta.confidence !== undefined ? `<span class="badge conf-badge ${confClass}">${meta.confidence}% Confidence</span>` : ""}
        ${meta.source && meta.source !== "None" ? `<span class="source-tag">Source: ${meta.source}</span>` : ""}
      </div>
    `;
  }

  msgDiv.innerHTML = `
    <div class="avatar">${role === "user" ? "👤" : "🤖"}</div>
    <div class="message-content">${contentHtml}</div>
  `;

  chatContainer.appendChild(msgDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showTypingIndicator() {
  const chatContainer = document.getElementById("chat-messages");
  const indicator = document.createElement("div");
  indicator.id = "typing-indicator";
  indicator.className = "message bot-message fade-in";
  indicator.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="message-content typing-dots">
      <span></span><span></span><span></span>
    </div>
  `;
  chatContainer.appendChild(indicator);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.remove();
}

function formatText(text) {
  if (!text) return "";
  return text
    .replace(/\n/g, "<br>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

// ------------------------------------------------------------------
// Main Chat Communication (Server First + Client Fallback)
// ------------------------------------------------------------------
async function sendMessageToBackend(userMessage) {
  showTypingIndicator();
  const startTime = Date.now();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        history: chatHistory,
        session_state: sessionState
      })
    });

    if (!res.ok) throw new Error("Server error");
    const data = await res.json();
    
    const elapsedTime = Date.now() - startTime;
    const delayNeeded = Math.max(0, 600 - elapsedTime);

    setTimeout(() => {
      removeTypingIndicator();
      sessionState = data.session_state || {};
      chatHistory.push({ role: "user", content: userMessage });
      chatHistory.push({ role: "assistant", content: data.answer, subject: data.subject || null });
      appendMessage("bot", data.answer, {
        intent: data.intent,
        confidence: data.confidence,
        source: data.source,
        options: data.options || []
      });
      updateInspector(data);
    }, delayNeeded);

  } catch (err) {
    // ⚡ Fallback Client-side Engine (Runs offline / zero-server seamlessly on any PC)
    setTimeout(() => {
      removeTypingIndicator();
      const fallbackData = processOfflineQuery(userMessage);
      chatHistory.push({ role: "user", content: userMessage });
      chatHistory.push({ role: "assistant", content: fallbackData.answer });
      appendMessage("bot", fallbackData.answer, {
        intent: fallbackData.intent,
        confidence: fallbackData.confidence,
        source: fallbackData.source,
        options: fallbackData.options || []
      });
      updateInspector(fallbackData);
    }, 500);
  }
}

// ------------------------------------------------------------------
// Embedded Client-Side Engine for Zero-Server Fallback
// ------------------------------------------------------------------
function processOfflineQuery(userMsg) {
  const q = userMsg.lower ? userMsg.lower().trim() : userMsg.toLowerCase().trim();

  // Greetings
  if (["hi", "hello", "hey", "good morning", "good evening"].some(g => q.includes(g))) {
    return { answer: "Hello! Welcome to GDG On Campus AI Assistant. How can I help you today?", intent: "GREETING", confidence: 99, source: "Greeting" };
  }

  // Name Query
  if (q.includes("remember my name") || q.includes("what is my name")) {
    const name = sessionState.name || null;
    return { answer: name ? `Yes, I remember your name! Your name is **${name}**.` : "I don't have your name stored in this conversation.", intent: "MEMORY_QUERY", confidence: 98, source: "Session Memory" };
  }

  // Founding
  if (q.includes("founded") || q.includes("start") || q.includes("begin") || q.includes("year")) {
    return { answer: "GDG On Campus was **founded in 2022**. It is a community of 150+ tech enthusiasts.", intent: "FAQ", confidence: 96, source: "Club Introduction" };
  }

  // Teams
  if (q.includes("team") && (q.includes("available") || q.includes("list") || q.includes("what"))) {
    return { answer: "The available teams in GDG On Campus are:\n\n• **AIML** (Lead: Rahul Sharma)\n• **Web Dev** (Lead: Priya Patel)\n• **App Dev** (Lead: Arjun Mehta)\n• **Cloud** (Lead: Sneha Gupta)\n• **Cybersecurity** (Lead: Vikram Singh)\n• **Design** (Lead: Ananya Reddy)", intent: "FAQ", confidence: 98, source: "Teams" };
  }

  if (q.includes("aiml")) return { answer: "The lead for **AIML** is **Rahul Sharma**.", intent: "FAQ", confidence: 98, source: "Teams → AIML" };
  if (q.includes("web")) return { answer: "The lead for **Web Dev** is **Priya Patel**.", intent: "FAQ", confidence: 98, source: "Teams → Web Dev" };
  if (q.includes("app")) return { answer: "The lead for **App Dev** is **Arjun Mehta**.", intent: "FAQ", confidence: 98, source: "Teams → App Dev" };
  if (q.includes("cloud") && !q.includes("jam")) return { answer: "The lead for **Cloud** is **Sneha Gupta**.", intent: "FAQ", confidence: 98, source: "Teams → Cloud" };
  if (q.includes("cyber") || q.includes("ctf")) return { answer: "The lead for **Cybersecurity** is **Vikram Singh**.", intent: "FAQ", confidence: 98, source: "Teams → Cybersecurity" };
  if (q.includes("design")) return { answer: "The lead for **Design** is **Ananya Reddy**.", intent: "FAQ", confidence: 98, source: "Teams → Design" };

  // Events & Dates
  if (q.includes("september 20") || q.includes("sept 20") || q.includes("20th")) {
    return { answer: "**Cloud Study Jam**\n• **Date**: Sept 20, 2025\n• **Status**: Upcoming", intent: "EVENT_INQUIRY", confidence: 96, source: "Events → Cloud Study Jam" };
  }
  if (q.includes("event") || q.includes("upcoming") || q.includes("workshop")) {
    return { answer: "Upcoming GDG On Campus Events:\n\n• **Intro to GenAI Workshop** — Sept 15, 2025\n• **Cloud Study Jam** — Sept 20, 2025\n• **Design Thinking Bootcamp** — Sept 25, 2025\n• **HackFest 2025** — Oct 10, 2025\n• **CyberCTF Challenge** — Nov 5, 2025", intent: "EVENT_INQUIRY", confidence: 97, source: "Events" };
  }

  // Recruitment
  if (q.includes("join") || q.includes("apply") || q.includes("recruitment") || q.includes("process")) {
    return { answer: "**GDG Recruitment Guidelines**:\n• **Window**: Sept 1–15, 2025\n• **Eligibility**: 1st to 3rd year\n• **Process**: Application Form → Technical Assessment (1 week) → Interview (15 min) → Results (1 week) → Onboarding (2 weeks)", intent: "FAQ", confidence: 96, source: "Recruitment" };
  }

  // Contacts
  if (q.includes("president") || q.includes("contact") || q.includes("email")) {
    return { answer: "The GDG On Campus **President** is **Aditya Kumar** (email: president@gdgoncampus.com).", intent: "FAQ", confidence: 96, source: "Contacts" };
  }

  // Rules
  if (q.includes("rule") || q.includes("active") || q.includes("policy")) {
    return { answer: "**GDG On Campus Rules**:\n• Minimum 2 events/month to stay active.\n• Inactive for 2 months = alumni status.\n• Team switching once per semester.\n• At least 1 project contribution per semester.", intent: "FAQ", confidence: 96, source: "Rules" };
  }

  // Strict Fallback
  return { answer: "I have no idea about that. I can only answer questions grounded in our official GDG On Campus club information.", intent: "UNKNOWN", confidence: 20, source: "None" };
}

function updateInspector(data) {
  document.getElementById("insp-intent").innerText = data.intent || "UNKNOWN";
  document.getElementById("insp-conf-bar").style.width = `${data.confidence || 0}%`;
  document.getElementById("insp-conf-text").innerText = `${data.confidence || 0}% Confidence`;
  document.getElementById("insp-source").innerText = data.source || "None";
  document.getElementById("insp-subject").innerText = data.subject || "General Context";
}

function resetInspector() {
  document.getElementById("insp-intent").innerText = "Waiting...";
  document.getElementById("insp-conf-bar").style.width = "0%";
  document.getElementById("insp-conf-text").innerText = "0%";
  document.getElementById("insp-source").innerText = "None";
  document.getElementById("insp-subject").innerText = "General";
}

async function loadDashboardData() {
  try {
    const statsRes = await fetch(`${API_BASE}/api/dashboard/stats`);
    const stats = await statsRes.json();

    document.getElementById("kpi-total-chats").innerText = stats.total_chats || 0;
    document.getElementById("kpi-successful").innerText = stats.successful_queries || 0;
    document.getElementById("kpi-actions").innerText = stats.actions_completed || 0;
    document.getElementById("kpi-unanswered").innerText = stats.unanswered_queries || 0;

    renderIntentChart(stats.intent_counts || {});
    renderGroundingChart(stats.successful_queries || 0, stats.unanswered_queries || 0);

    const actionsRes = await fetch(`${API_BASE}/api/dashboard/actions`);
    const actions = await actionsRes.json();
    renderActionsTable(actions.registrations || [], actions.feedback_entries || []);

    const unansRes = await fetch(`${API_BASE}/api/dashboard/unanswered`);
    const unanswered = await unansRes.json();
    renderUnansweredTable(unanswered || []);

  } catch (err) {
    // Offline fallback for stats
    document.getElementById("kpi-total-chats").innerText = chatHistory.length / 2;
    document.getElementById("kpi-successful").innerText = chatHistory.length / 2;
    renderIntentChart({ "FAQ": 3, "EVENT_INQUIRY": 1, "GREETING": 1 });
    renderGroundingChart(5, 0);
  }
}

function renderIntentChart(intentCounts) {
  const ctx = document.getElementById("intentChart").getContext("2d");
  const labels = ["GREETING", "FAQ", "EVENT_INQUIRY", "ACTION_REQUEST", "UNKNOWN"];
  const dataValues = labels.map(l => intentCounts[l] || 0);

  if (intentChartInstance) intentChartInstance.destroy();

  intentChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: dataValues.some(v => v > 0) ? dataValues : [1, 0, 0, 0, 0],
        backgroundColor: ["#4285F4", "#34A853", "#FBBC04", "#A855F7", "#EA4335"],
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { color: "#94A3B8", font: { family: "Outfit" } } }
      }
    }
  });
}

function renderGroundingChart(successful, unanswered) {
  const ctx = document.getElementById("groundingChart").getContext("2d");
  if (groundingChartInstance) groundingChartInstance.destroy();

  groundingChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Grounded Solved", "Unanswered"],
      datasets: [{
        data: [successful, unanswered],
        backgroundColor: ["#34A853", "#EA4335"],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: "#94A3B8" }, grid: { display: false } },
        y: { ticks: { color: "#94A3B8", stepSize: 1 }, grid: { color: "rgba(255,255,255,0.05)" } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function renderActionsTable(registrations, feedbackEntries) {
  const tbody = document.querySelector("#registrations-table tbody");
  const combined = [];

  registrations.forEach(r => {
    combined.push({
      type: "Event Registration",
      id: r.ticket_id,
      name: r.name,
      email: r.email,
      details: `${r.event_title} (${r.year})`,
      timestamp: r.timestamp
    });
  });

  feedbackEntries.forEach(f => {
    combined.push({
      type: "Feedback",
      id: f.id,
      name: f.email,
      email: f.email,
      details: f.message,
      timestamp: f.timestamp
    });
  });

  if (combined.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#94A3B8;">No actions logged yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = combined.map(item => `
    <tr>
      <td><code>${item.id}</code></td>
      <td><strong>${item.name}</strong></td>
      <td>${item.email}</td>
      <td><span class="badge conf-badge high">${item.details}</span></td>
      <td style="color:#94A3B8;">${item.timestamp}</td>
    </tr>
  `).join("");
}

function renderUnansweredTable(unanswered) {
  const tbody = document.querySelector("#unanswered-table tbody");
  if (!unanswered || unanswered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#94A3B8;">No unanswered queries logged yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = unanswered.map(u => `
    <tr>
      <td><code>${u.id}</code></td>
      <td>${u.query}</td>
      <td><span class="badge conf-badge low">${u.confidence}%</span></td>
      <td style="color:#94A3B8;">${u.timestamp}</td>
    </tr>
  `).join("");
}

async function loadKnowledgeBase() {
  try {
    const res = await fetch(`${API_BASE}/api/knowledge`);
    const data = await res.json();
    renderKnowledgeGrid(data);
  } catch (err) {
    // Offline default data rendering
    const fallbackKB = {
      "Introduction": "GDG On Campus is a community of 150+ tech enthusiasts. Founded in 2022. Organizes workshops, hackathons, and speaker sessions.",
      "Teams": [
        { "name": "AIML", "lead": "Rahul Sharma" },
        { "name": "Web Dev", "lead": "Priya Patel" },
        { "name": "App Dev", "lead": "Arjun Mehta" },
        { "name": "Cloud", "lead": "Sneha Gupta" },
        { "name": "Cybersecurity", "lead": "Vikram Singh" },
        { "name": "Design", "lead": "Ananya Reddy" }
      ],
      "Events": [
        { "title": "Intro to GenAI Workshop", "date": "Sept 15, 2025", "status": "Upcoming" },
        { "title": "Cloud Study Jam", "date": "Sept 20, 2025", "status": "Upcoming" },
        { "title": "Design Thinking Bootcamp", "date": "Sept 25, 2025", "status": "Upcoming" },
        { "title": "HackFest 2025", "date": "Oct 10, 2025", "status": "Upcoming" },
        { "title": "CyberCTF Challenge", "date": "Nov 5, 2025", "status": "Upcoming" }
      ],
      "Recruitment": "Application Form → Technical Assessment (1 week) → Interview (15 min) → Results (1 week) → Onboarding (2 weeks). Window: Sept 1–15, 2025. Eligibility: 1st to 3rd year.",
      "Rules": ["Minimum 2 events/month to stay active.", "Inactive for 2 months = alumni status.", "Team switching once per semester."],
      "Contacts": ["President: Aditya Kumar (president@gdgoncampus.com)", "VP: Meera Joshi", "Tech Head: Rohan Desai", "General: info@gdgoncampus.com"],
      "Achievements": ["Best Community Award at DevFest 2024", "12 open-source projects", "25+ workshops"]
    };
    renderKnowledgeGrid(fallbackKB);
  }
}

function renderKnowledgeGrid(data) {
  const container = document.getElementById("kb-category-container");
  if (!container) return;
  container.innerHTML = "";

  Object.keys(data).forEach(category => {
    const card = document.createElement("div");
    card.className = "category-card";
    card.innerHTML = `
      <h3>📌 ${category}</h3>
      <pre>${JSON.stringify(data[category], null, 2)}</pre>
    `;
    container.appendChild(card);
  });
}
