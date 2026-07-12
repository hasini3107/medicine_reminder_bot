// ============================================================
// static/js/medicines.js
//
// Responsibilities:
//   - Render the medicines data table with search + filter.
//   - Open the Add / Edit modal and pre-fill fields.
//   - Save (add or update) a medicine record.
//   - Delete a medicine record.
//
// Depends on: utils.js
// Reads/writes global state: medicines[]  (defined in app.js)
// ============================================================


// Module-level variable to track which medicine is being edited
// (null = Add mode, number = Edit mode for that id).
let editingMedId = null;


// ------------------------------------------------------------------
// Table rendering
// ------------------------------------------------------------------
/**
 * (Re)render the medicines table.
 * Applies text search and status filter simultaneously.
 *
 * @param {string} [filter=""]  - Lower-case search string.
 */
function renderMedicinesTable(filter = "") {
    const tbody        = document.getElementById("med-table-body");
    if (!tbody) return;

    const statusFilter = document.getElementById("med-filter")?.value || "";
    tbody.innerHTML    = "";

    const filtered = medicines.filter((m) => {
        const matchText =
            !filter ||
            m.name.toLowerCase().includes(filter) ||
            m.generic.toLowerCase().includes(filter);
        const matchStatus = !statusFilter || m.status === statusFilter;
        return matchText && matchStatus;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `
        <tr>
            <td colspan="7" style="text-align:center;color:var(--text-muted);padding:30px;">
                No medicines found.
            </td>
        </tr>`;
        return;
    }

    filtered.forEach((m, i) => {
        tbody.innerHTML += `
        <tr>
            <td style="color:var(--text-muted)">${i + 1}</td>
            <td><strong style="color:var(--text-primary)">${m.name}</strong></td>
            <td>${m.generic}</td>
            <td>${m.dosage}</td>
            <td>${m.when}</td>
            <td><span class="status-badge ${m.status}">${m.status}</span></td>
            <td>
                <div class="action-btns">
                    <button class="action-btn edit"
                            onclick="openEditMedModal(${m.id})"
                            title="Edit">
                        <i class="fa-solid fa-pen"></i>
                    </button>
                    <button class="action-btn del"
                            onclick="deleteMedicine(${m.id})"
                            title="Delete">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    });
}

/** Live search — called by the search input's oninput handler. */
function filterMedicines() {
    const q = document.getElementById("med-search")?.value.toLowerCase() || "";
    renderMedicinesTable(q);
}


// ------------------------------------------------------------------
// Modal — Add
// ------------------------------------------------------------------
function openAddMedModal() {
    editingMedId = null;
    document.getElementById("modal-title").textContent = "Add Medicine";

    // Clear all form fields
    ["form-med-name", "form-generic", "form-dosage", "form-when", "form-uses"]
        .forEach((id) => { document.getElementById(id).value = ""; });
    document.getElementById("form-status").value = "Active";

    document.getElementById("med-modal").classList.add("show");
}


// ------------------------------------------------------------------
// Modal — Edit
// ------------------------------------------------------------------
/**
 * Open the modal pre-filled with the selected medicine's data.
 * @param {number} id
 */
function openEditMedModal(id) {
    const m = medicines.find((x) => x.id === id);
    if (!m) return;

    editingMedId = id;
    document.getElementById("modal-title").textContent = "Edit Medicine";

    document.getElementById("form-med-name").value = m.name;
    document.getElementById("form-generic").value  = m.generic;
    document.getElementById("form-dosage").value   = m.dosage;
    document.getElementById("form-when").value     = m.when;
    document.getElementById("form-uses").value     = m.uses;
    document.getElementById("form-status").value   = m.status;

    document.getElementById("med-modal").classList.add("show");
}


// ------------------------------------------------------------------
// Save (add or update)
// ------------------------------------------------------------------
async function saveMedicine() {
    const name = document.getElementById("form-med-name").value.trim();
    if (!name) {
        showToast("❌ Medicine name is required", "error");
        return;
    }

    const data = {
        name,
        generic: document.getElementById("form-generic").value.trim(),
        dosage:  document.getElementById("form-dosage").value.trim(),
        when:    document.getElementById("form-when").value.trim(),
        uses:    document.getElementById("form-uses").value.trim(),
        status:  document.getElementById("form-status").value,
    };

    if (editingMedId !== null) {
        // Update existing
        const idx = medicines.findIndex((m) => m.id === editingMedId);
        if (idx !== -1) medicines[idx] = { ...medicines[idx], ...data };
        showToast("✅ Medicine updated successfully");
    } else {
        // Add new
        data.id = Date.now();
        medicines.push(data);
        showToast("✅ Medicine added successfully");
    }

    // Save to backend
    try {
        const response = await fetch('/api/medicines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ medicines })
        });
        if (response.ok) {
            localStorage.setItem('mediassist-medicines', JSON.stringify(medicines));
        }
    } catch (error) {
        console.error('Failed to save medicines to backend:', error);
        // Fallback to localStorage
        localStorage.setItem('mediassist-medicines', JSON.stringify(medicines));
    }

    closeModal("med-modal");
    renderMedicinesTable();
    updateDashboardStats();
    updateProfileUI();          // update medicine count in profile
    populateReminderSelect();   // keep reminder dropdown in sync
}


// ------------------------------------------------------------------
// Delete
// ------------------------------------------------------------------
/**
 * Remove a medicine after confirmation.
 * @param {number} id
 */
async function deleteMedicine(id) {
    if (!confirm("Are you sure you want to delete this medicine?")) return;
    medicines = medicines.filter((m) => m.id !== id);
    
    // Save to backend
    try {
        const response = await fetch('/api/medicines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ medicines })
        });
        if (response.ok) {
            localStorage.setItem('mediassist-medicines', JSON.stringify(medicines));
        }
    } catch (error) {
        console.error('Failed to save medicines to backend:', error);
        localStorage.setItem('mediassist-medicines', JSON.stringify(medicines));
    }

    renderMedicinesTable();
    updateDashboardStats();
    updateProfileUI();          // update medicine count in profile
    showToast("🗑️ Medicine deleted");
}
