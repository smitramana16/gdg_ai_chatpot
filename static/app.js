let chatHistory = [];
let sessionState = {};
let intentChartInstance = null;
let groundingChartInstance = null;

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

async function sendMessageToBackend(userMessage) {
  showTypingIndicator();

  // 600ms artificial delay for smooth natural feel
  const startTime = Date.now();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        history: chatHistory,
        session_state: sessionState
      })
    });

    const data = await res.json();
    const elapsedTime = Date.now() - startTime;
    const delayNeeded = Math.max(0, 600 - elapsedTime);

    setTimeout(() => {
      removeTypingIndicator();

      sessionState = data.session_state || {};

      chatHistory.push({ role: "user", content: userMessage });
      chatHistory.push({
        role: "assistant",
        content: data.answer,
        subject: data.subject || null
      });

      appendMessage("bot", data.answer, {
        intent: data.intent,
        confidence: data.confidence,
        source: data.source
      });

      updateInspector(data);
    }, delayNeeded);

  } catch (err) {
    removeTypingIndicator();
    appendMessage("bot", "⚠️ Error connecting to server.");
  }
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
    const statsRes = await fetch("/api/dashboard/stats");
    const stats = await statsRes.json();

    document.getElementById("kpi-total-chats").innerText = stats.total_chats || 0;
    document.getElementById("kpi-successful").innerText = stats.successful_queries || 0;
    document.getElementById("kpi-actions").innerText = stats.actions_completed || 0;
    document.getElementById("kpi-unanswered").innerText = stats.unanswered_queries || 0;

    renderIntentChart(stats.intent_counts || {});
    renderGroundingChart(stats.successful_queries || 0, stats.unanswered_queries || 0);

    const actionsRes = await fetch("/api/dashboard/actions");
    const actions = await actionsRes.json();
    renderActionsTable(actions.registrations || [], actions.feedback_entries || []);

    const unansRes = await fetch("/api/dashboard/unanswered");
    const unanswered = await unansRes.json();
    renderUnansweredTable(unanswered || []);

  } catch (err) {
    console.error("Dashboard error", err);
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
    const res = await fetch("/api/knowledge");
    const data = await res.json();
    const container = document.getElementById("kb-category-container");
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
  } catch (err) {
    console.error("KB load error", err);
  }
}
