// ============================================================
// static/js/reminders.js
//
// Responsibilities:
//   - Render the reminders list.
//   - Toggle completion status of reminders (taken vs pending).
//   - Delete reminders.
//   - Save reminders.
//   - Populate the medicine select dropdown inside the reminder modal.
//
// Reads/writes global state: reminders[], medicines[] (defined in app.js)
// ============================================================


// ------------------------------------------------------------------
// Render
// ------------------------------------------------------------------
function renderReminderList() {
    const container = document.getElementById("reminder-list-display");
    if (!container) return;

    container.innerHTML = "";

    if (reminders.length === 0) {
        container.innerHTML = `
        <p style="color:var(--text-muted);text-align:center;padding:20px;">
            No reminders set. Click "Add Reminder" to get started.
        </p>`;
        return;
    }

    const sorted = [...reminders].sort((a, b) => a.time.localeCompare(b.time));

    sorted.forEach((r) => {
        const freq = r.freq || r.frequency || 'Daily';
        const note = r.note || r.notes || 'No notes';
        container.innerHTML += `
        <div class="reminder-item" id="rem-${r.id}">
            <div class="rem-time-badge">${formatTime12(r.time)}</div>
            <div class="rem-info">
                <div class="rem-name">${r.medName}</div>
                <div class="rem-note">${freq} • ${note}</div>
            </div>
            <button class="rem-status-toggle ${r.done ? "done" : ""}"
                    onclick="toggleReminderDone(${r.id})"
                    title="${r.done ? "Mark as pending" : "Mark as taken"}">
                ${r.done ? '<i class="fa-solid fa-check"></i>' : ""}
            </button>
            <button class="action-btn del"
                    onclick="deleteReminder(${r.id})"
                    title="Delete">
                <i class="fa-solid fa-trash"></i>
            </button>
        </div>`;
    });
}


// ------------------------------------------------------------------
// Toggle / Complete
// ------------------------------------------------------------------
/**
 * Toggle between taken (done=true) and pending (done=false).
 * @param {number} id
 */
function toggleReminderDone(id) {
    const r = reminders.find((x) => x.id === id);
    if (!r) return;

    r.done = !r.done;

    renderReminderList();
    syncRemindersToBackend();

    // Sync other components
    if (typeof renderSchedule === "function") renderSchedule();
    if (typeof updateDashboardStats === "function") updateDashboardStats();

    showToast(r.done ? "✅ Marked as taken" : "🔄 Marked as pending");
}


// ------------------------------------------------------------------
// Add / Save
// ------------------------------------------------------------------
function openAddReminderModal() {
    populateReminderSelect();
    document.getElementById("reminder-time").value = "";
    document.getElementById("reminder-note").value = "";
    document.getElementById("reminder-modal").classList.add("show");
}

/** Populate dropdown with active medicines. */
function populateReminderSelect() {
    const sel = document.getElementById("reminder-med-select");
    if (!sel) return;

    sel.innerHTML = "";

    const activeMeds = medicines.filter((m) => m.status === "Active");
    if (activeMeds.length === 0) {
        sel.innerHTML = `<option value="">No active medicines</option>`;
        return;
    }

    activeMeds.forEach((m) => {
        sel.innerHTML += `
        <option value="${m.id}" data-name="${m.name}">
            ${m.name}
        </option>`;
    });
}

function saveReminder() {
    const sel  = document.getElementById("reminder-med-select");
    const time = document.getElementById("reminder-time").value;

    if (!sel || !sel.value) {
        showToast("❌ Please add an active medicine first", "error");
        return;
    }
    if (!time) {
        showToast("❌ Please select a time", "error");
        return;
    }

    const medId   = parseInt(sel.value, 10);
    const medName = sel.options[sel.selectedIndex]?.dataset.name || "";

    reminders.push({
        id: Date.now(),
        medId,
        medName,
        time,
        freq: document.getElementById("reminder-freq").value,
        note: document.getElementById("reminder-note").value || "No notes",
        done: false,
    });

    closeModal("reminder-modal");
    renderReminderList();
    syncRemindersToBackend();

    // Sync other components
    if (typeof renderSchedule === "function") renderSchedule();
    if (typeof updateDashboardStats === "function") updateDashboardStats();

    showToast("✅ Reminder saved");
}


// ------------------------------------------------------------------
// Delete
// ------------------------------------------------------------------
/**
 * Remove a reminder from the schedule.
 * @param {number} id
 */
function deleteReminder(id) {
    if (!confirm("Are you sure you want to delete this reminder?")) return;

    reminders = reminders.filter((r) => r.id !== id);

    renderReminderList();
    syncRemindersToBackend();

    // Sync other components
    if (typeof renderSchedule === "function") renderSchedule();
    if (typeof updateDashboardStats === "function") updateDashboardStats();

    showToast("🗑️ Reminder deleted");
}

// ------------------------------------------------------------------
// API Sync
// ------------------------------------------------------------------
async function syncRemindersToBackend() {
    try {
        const response = await fetch('/api/reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reminders })
        });
        if (response.ok) {
            localStorage.setItem('mediassist-reminders', JSON.stringify(reminders));
        }
    } catch (error) {
        console.error('Failed to save reminders to backend:', error);
        localStorage.setItem('mediassist-reminders', JSON.stringify(reminders));
    }
}
