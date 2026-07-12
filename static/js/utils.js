// ============================================================
// static/js/utils.js
//
// Shared helper functions used across ALL other JS modules.
// Load this file FIRST in index.html.
// ============================================================


// ------------------------------------------------------------------
// Toast notification
// ------------------------------------------------------------------
/**
 * Show a brief pop-up message at the bottom-right of the screen.
 * @param {string} msg   - Text to display (emojis welcome).
 * @param {string} type  - 'success' (default) | 'error'
 */
function showToast(msg, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.style.background = type === "error" ? "#e63946" : "#1a1d3b";
    toast.classList.add("show");
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => toast.classList.remove("show"), 3000);
}


// ------------------------------------------------------------------
// HTML escaping (prevent XSS when rendering user input)
// ------------------------------------------------------------------
/**
 * Escape special HTML characters in a plain string.
 * @param {string} text
 * @returns {string}
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}


// ------------------------------------------------------------------
// Time formatting
// ------------------------------------------------------------------
/**
 * Format a Date object as "HH:MM AM/PM".
 * @param {Date} date
 * @returns {string}
 */
function formatTime(date) {
    return date.toLocaleTimeString("en-IN", {
        hour:   "2-digit",
        minute: "2-digit",
    });
}

/**
 * Convert "HH:MM" (24-hour) to "H:MM AM/PM".
 * @param {string} time24  e.g. "14:30"
 * @returns {string}       e.g. "2:30 PM"
 */
function formatTime12(time24) {
    const [h, m]  = time24.split(":");
    const hour    = parseInt(h, 10);
    const ampm    = hour >= 12 ? "PM" : "AM";
    const display = hour > 12 ? hour - 12 : hour || 12;
    return `${display}:${m} ${ampm}`;
}


// ------------------------------------------------------------------
// Dark-mode toggle (persists in localStorage)
// ------------------------------------------------------------------
function toggleDarkMode() {
    const isDark = document.getElementById("dark-mode-toggle").checked;
    document.documentElement.setAttribute("data-theme", isDark ? "dark" : "");
    localStorage.setItem("mediassist-dark", isDark ? "1" : "");

    // Redraw dashboard canvas with updated CSS variables
    setTimeout(() => {
        if (typeof drawDonut === "function") {
            drawDonut("intakeDonut", 85, 15, 0);
        }
    }, 60);
}

/**
 * Restore the persisted dark-mode preference on page load.
 * Called from app.js inside DOMContentLoaded.
 */
function restoreDarkMode() {
    if (localStorage.getItem("mediassist-dark") === "1") {
        document.documentElement.setAttribute("data-theme", "dark");
        const toggle = document.getElementById("dark-mode-toggle");
        if (toggle) toggle.checked = true;
    }
}


// ------------------------------------------------------------------
// Modal helpers
// ------------------------------------------------------------------
/**
 * Close any modal overlay by ID.
 * @param {string} id  - The modal overlay element's id.
 */
function closeModal(id) {
    document.getElementById(id).classList.remove("show");
}

// Close modals when clicking the semi-transparent backdrop
document.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
        e.target.classList.remove("show");
    }
});
