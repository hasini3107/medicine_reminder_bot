// ============================================================
// static/js/chatbot.js
//
// Responsibilities:
//   - Manage the medical AI assistant chat panel.
//   - Send users' messages to the POST /chat route.
//   - Render user/bot messages (with basic markdown bold formatting).
//   - Show/hide typing indicators.
//   - Manage recent queries list and chips.
//   - Speech recognition (voice input).
//
// Depends on: utils.js
// Reads/writes global state: recentQueries[] (defined in app.js)
// ============================================================


// ------------------------------------------------------------------
// Main Chat Logic
// ------------------------------------------------------------------
async function sendMessage() {
    const chatBox = document.getElementById("chat-box");
    const input   = document.getElementById("user-input");
    if (!input || !chatBox) return;

    const message = input.value.trim();
    if (!message) return;

    // Hide suggestions once user interacts
    const suggestions = document.getElementById("chat-suggestions");
    if (suggestions) suggestions.style.display = "none";

    // Append user's text to viewport & clear input field
    appendUserMessage(message);
    input.value = "";

    // Log query in sidebar
    addRecentQuery(message);

    // Show typing state
    const typingId = appendTyping();

    try {
        const response = await fetch("/chat", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ message }),
        });

        const data = await response.json();
        removeTyping(typingId);
        appendBotMessage(data.reply);

    } catch (err) {
        console.error("[CHAT_ERR]", err);
        removeTyping(typingId);
        appendBotMessage(
            "❌ Unable to connect to the server. " +
            "Please make sure the Flask backend and Ollama model are running."
        );
    }
}


// ------------------------------------------------------------------
// Message rendering
// ------------------------------------------------------------------
function appendUserMessage(text) {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    const div     = document.createElement("div");
    div.className = "user-msg-wrap";
    div.innerHTML = `<div class="user-message">${escapeHtml(text)}</div>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function appendBotMessage(text) {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    const div     = document.createElement("div");
    div.className = "bot-msg-wrap";

    // Format markdown-like bold (**text**) and handle line breaks safely
    const formatted = escapeHtml(text)
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");

    div.innerHTML = `
    <div class="bot-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="bot-message">
        <strong>MediAssist Assistant</strong>
        <p>${formatted}</p>
        <div class="msg-time">${formatTime(new Date())}</div>
    </div>`;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}


// ------------------------------------------------------------------
// Typing Indicator
// ------------------------------------------------------------------
function appendTyping() {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return "";

    const id      = "typing-" + Date.now();
    const div     = document.createElement("div");
    div.className = "bot-msg-wrap";
    div.id        = id;
    div.innerHTML = `
    <div class="bot-avatar"><i class="fa-solid fa-robot"></i></div>
    <div class="bot-message">
        <strong>MediAssist Assistant</strong>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    </div>`;

    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}


// ------------------------------------------------------------------
// Clear Chat / Suggestions
// ------------------------------------------------------------------
function clearChat() {
    const chatBox = document.getElementById("chat-box");
    if (!chatBox) return;

    chatBox.innerHTML = `
    <div class="bot-msg-wrap">
        <div class="bot-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bot-message">
            <strong>MediAssist Assistant</strong>
            <p>Chat history cleared. How can I help you today?</p>
            <div class="msg-time">${formatTime(new Date())}</div>
        </div>
    </div>`;

    // Show suggestions again
    const suggestions = document.getElementById("chat-suggestions");
    if (suggestions) suggestions.style.display = "flex";

    // Clear chips
    recentQueries = [];
    const queriesContainer = document.getElementById("recent-queries");
    if (queriesContainer) {
        queriesContainer.innerHTML = `
        <p style="color:var(--text-muted);font-size:13px;">No recent queries</p>`;
    }
}

function useSuggestion(el) {
    const input = document.getElementById("user-input");
    if (input) {
        input.value = el.textContent.trim();
        sendMessage();
    }
}

function addRecentQuery(q) {
    recentQueries.unshift(q);
    if (recentQueries.length > 5) recentQueries.pop();

    const container = document.getElementById("recent-queries");
    if (!container) return;

    container.innerHTML = recentQueries.map((rq) => {
        const safeQ = rq.replace(/'/g, "\\'");
        return `
        <span class="recent-chip"
              onclick="const inp=document.getElementById('user-input'); if(inp){inp.value='${safeQ}'; inp.focus();}">
            ${escapeHtml(rq)}
        </span>`;
    }).join("");
}


// ------------------------------------------------------------------
// Voice Recognition / Microphone
// ------------------------------------------------------------------
let recognition = null;

function toggleMic() {
    const btn = document.getElementById("mic-btn");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        showToast("❌ Speech recognition not supported in this browser", "error");
        return;
    }

    if (recognition) {
        recognition.stop();
        recognition = null;
        if (btn) btn.classList.remove("listening");
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-IN";

    recognition.onresult = function (e) {
        const input = document.getElementById("user-input");
        if (input && e.results[0][0]) {
            input.value = e.results[0][0].transcript;
        }
    };

    recognition.onend = function () {
        if (btn) btn.classList.remove("listening");
        recognition = null;
    };

    recognition.start();
    if (btn) btn.classList.add("listening");
}


// ------------------------------------------------------------------
// Keyboard / Input setup (attach listeners if elements exist)
// ------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("user-input");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }
});
