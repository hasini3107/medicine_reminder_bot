// ============================================================
// static/js/navigation.js
//
// Responsibilities:
//   - Switch between pages (sidebar links).
//   - Toggle the mobile sidebar open/close.
//   - Notification dropdown open/close.
// ============================================================


// ------------------------------------------------------------------
// Page switching
// ------------------------------------------------------------------
/**
 * Show a named page and highlight its sidebar link.
 *
 * @param {string}      page   - Page key: 'dashboard' | 'medicines' |
 *                               'reminders' | 'chatbot' | 'reports' |
 *                               'profile' | 'settings'
 * @param {HTMLElement} navEl  - The <a class="nav-item"> that was clicked.
 */
function showPage(page, navEl) {
    // Hide all pages, deactivate all nav links
    document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));

    // Activate selected page
    const target = document.getElementById("page-" + page);
    if (target) target.classList.add("active");
    if (navEl)  navEl.classList.add("active");

    // Update breadcrumb label
    const labels = {
        dashboard: "HOME PAGE",
        medicines: "MY MEDICINES",
        reminders: "REMINDERS",
        chatbot:   "MEDICINE ASSISTANT",
        reports:   "REPORTS",
        profile:   "PROFILE",
        settings:  "SETTINGS",
    };
    document.getElementById("page-breadcrumb").textContent =
        labels[page] || "PAGE";

    // Close sidebar on mobile after navigation
    if (window.innerWidth < 900) closeSidebar();

    // Trigger page-specific initialisation
    _onPageEnter(page);
}

/**
 * Called every time a page becomes visible.
 * Delegates to the relevant module's init function.
 */
function _onPageEnter(page) {
    switch (page) {
        case "dashboard":
            if (typeof updateDashboardStats === "function") updateDashboardStats();
            if (typeof renderSchedule       === "function") renderSchedule();
            break;
        case "medicines":
            if (typeof renderMedicinesTable === "function") renderMedicinesTable();
            break;
        case "reminders":
            if (typeof renderReminderList   === "function") renderReminderList();
            break;
        case "reports":
            if (typeof renderReportsList === "function") renderReportsList();
            break;
        case "profile":
            if (typeof updateProfileUI      === "function") updateProfileUI();
            break;
        case "chatbot":
            if (typeof updateChatIntro      === "function") updateChatIntro();
            break;
    }
}


// ------------------------------------------------------------------
// Sidebar toggle (mobile)
// ------------------------------------------------------------------
function toggleSidebar() {
    document.getElementById("sidebar").classList.toggle("open");
}

function closeSidebar() {
    document.getElementById("sidebar").classList.remove("open");
}


// ------------------------------------------------------------------
// Notification dropdown
// ------------------------------------------------------------------
function toggleNotif() {
    document.getElementById("notif-dropdown").classList.toggle("show");
}

// Close the dropdown when clicking anywhere outside it
document.addEventListener("click", (e) => {
    const dropdown = document.getElementById("notif-dropdown");
    const btn      = document.getElementById("notif-btn");
    if (btn && !btn.contains(e.target)) {
        dropdown.classList.remove("show");
    }
});
