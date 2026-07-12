// ============================================================
// static/js/dashboard.js
//
// Responsibilities:
//   - Populate the welcome date.
//   - Compute and display the four stats cards.
//   - Render "Today's Schedule" list.
//   - Show the "Next Reminder" banner.
//
// Depends on: utils.js, charts.js
// Reads global state: medicines[], reminders[]  (defined in app.js)
// ============================================================


// ------------------------------------------------------------------
// Entry point — called once on DOMContentLoaded (from app.js)
// ------------------------------------------------------------------
function initDashboard() {
    _setWelcomeDate();
    _setInitChatTime();
    updateDashboardStats();
    renderSchedule();
    // Draw chart using real data (will be 0/0 until user adds reminders)
    if (typeof updateChart === "function") updateChart();
}


// ------------------------------------------------------------------
// Welcome bar — date display
// ------------------------------------------------------------------
function _setWelcomeDate() {
    const el = document.getElementById("dashboard-date");
    if (!el) return;
    el.textContent = new Date().toLocaleDateString("en-IN", {
        weekday: "long",
        year:    "numeric",
        month:   "long",
        day:     "numeric",
    });
}

function _setInitChatTime() {
    const el = document.getElementById("init-time");
    if (el) el.textContent = formatTime(new Date());
}


// ------------------------------------------------------------------
// Stats cards
// ------------------------------------------------------------------
/**
 * Recompute taken / pending / missed totals from the live
 * reminders[] array and push them into the DOM.
 * Called every time a reminder status changes.
 */
function updateDashboardStats() {
    const activeCount = medicines.filter((m) => m.status === "Active").length;
    const taken       = reminders.filter((r) => r.done).length;
    const pending     = reminders.filter((r) => !r.done).length;

    document.getElementById("stat-total").textContent   = activeCount;
    document.getElementById("stat-taken").textContent   = taken;
    document.getElementById("stat-pending").textContent = pending;
    document.getElementById("stat-missed").textContent  = 0;
}


// ------------------------------------------------------------------
// Today's Schedule list
// ------------------------------------------------------------------
/**
 * Re-render the schedule list and next-reminder banner.
 * Called after reminders change (add, delete, toggle).
 */
function renderSchedule() {
    const list = document.getElementById("schedule-list");
    if (!list) return;

    list.innerHTML = "";

    if (reminders.length === 0) {
        list.innerHTML = `
        <div style="text-align:center;padding:20px;color:var(--text-muted);">
            <i class="fa-solid fa-calendar-plus" style="font-size:28px;margin-bottom:8px;opacity:.4;"></i>
            <p style="font-size:13px;">No reminders yet. <a href="#" onclick="showPage('reminders', document.getElementById('nav-reminders'));setTimeout(openAddReminderModal,100)" style="color:var(--primary);">Add one now</a>.</p>
        </div>`;
        // Hide next reminder banner
        const banner = document.getElementById("next-reminder-banner");
        if (banner) banner.style.display = "none";
        return;
    }

    const sorted = [...reminders].sort((a, b) => a.time.localeCompare(b.time));

    // Show at most 4 items
    sorted.slice(0, 4).forEach((r) => {
        const status = r.done ? "taken" : "pending";
        const label  = r.done ? "Taken" : "Pending";
        const dosage = _getMedDosage(r.medId);

        list.innerHTML += `
        <div class="schedule-item">
            <div class="sch-time">
                <div class="hour">${_hour12(r.time)}</div>
                <div>${_ampm(r.time)}</div>
            </div>
            <div class="sch-dot ${status}"></div>
            <div class="sch-info">
                <div class="sch-name">${r.medName}</div>
                <div class="sch-qty">${dosage}</div>
            </div>
            <span class="sch-badge ${status}">${label}</span>
        </div>`;
    });

    // Update the "Next Reminder" banner
    const banner = document.getElementById("next-reminder-banner");
    const next = sorted.find((r) => !r.done);
    if (next) {
        if (banner) banner.style.display = "";
        document.getElementById("next-med-name").textContent = next.medName;
        document.getElementById("next-med-time").textContent = formatTime12(next.time);
    } else {
        if (banner) banner.style.display = "none";
    }
}


// ------------------------------------------------------------------
// Private helpers
// ------------------------------------------------------------------
function _getMedDosage(medId) {
    const m = medicines.find((x) => x.id === medId);
    return m ? m.dosage : "";
}

function _hour12(time24) {
    const h = parseInt(time24.split(":")[0], 10);
    const d = h > 12 ? h - 12 : h || 12;
    return `${d}:${time24.split(":")[1]}`;
}

function _ampm(time24) {
    return parseInt(time24.split(":")[0], 10) >= 12 ? "PM" : "AM";
}
