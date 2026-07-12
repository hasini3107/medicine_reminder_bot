// ============================================================
// static/js/app.js
//
// The central coordinator for the MediAssist UI.
//   1. Declares global state variables.
//   2. Performs startup initialization on DOMContentLoaded.
//   3. Contains general global event-handlers (upload, profile).
// ============================================================


// ------------------------------------------------------------------
// Global App State (Available to all modules in the global namespace)
// ------------------------------------------------------------------
let medicines = [];

let reminders = [];

let recentQueries = [];
 
let reports = [];

// Profile data with defaults
let profileData = {
    name: "User",
    age: 0,
    email: "",
    phone: "",
    blood: "",
    doctor: "",
    conditions: "",
    allergies: ""
};


// ------------------------------------------------------------------
// Application Start (DOMContentLoaded)
// ------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
    // 1. Recover appearance settings (fast, no network)
    restoreDarkMode();

    // 2. Load profile data from localStorage as immediate fallback
    loadProfileData();

    // 3. Load user profile + all data from backend
    await loadUserProfile();
    await loadUserMedicines();
    await loadUserReminders();
    await loadUserReports();

    // 4. Load the initial Dashboard view
    if (typeof initDashboard === "function") {
        initDashboard();
    }

    // 5. Pre-fill the add reminder dropdown
    if (typeof populateReminderSelect === "function") {
        populateReminderSelect();
    }

    // 6. Sync medicines table if on medicines page
    if (typeof renderMedicinesTable === "function") {
        renderMedicinesTable();
    }

    // 7. Start the real-time reminder checker
    startReminderService();
});


// ------------------------------------------------------------------
// Real-time Reminders Background Loop
// ------------------------------------------------------------------
function startReminderService() {
    // Check every 30 seconds
    setInterval(() => {
        const now = new Date();
        const currentHourStr = now.getHours().toString().padStart(2, '0');
        const currentMinStr = now.getMinutes().toString().padStart(2, '0');
        const currentTime = `${currentHourStr}:${currentMinStr}`;
        
        reminders.forEach(r => {
            if (!r.done && r.time === currentTime) {
                // Prevent duplicate notifications within the same minute
                if (!r._notifiedTime || r._notifiedTime !== currentTime) {
                    r._notifiedTime = currentTime;
                    showToast(`⏰ REMINDER: It's time to take ${r.medName}!`, "info");
                    
                    // Attempt to play a subtle notification beep
                    try {
                        const audio = new Audio("https://actions.google.com/sounds/v1/alarms/beep_short.ogg");
                        audio.play().catch(e => console.log("Audio play prevented by browser interaction policies"));
                    } catch(err) {}
                }
            }
        });
    }, 30000);
}


// ------------------------------------------------------------------
// Page-specific general event-handlers
// ------------------------------------------------------------------

// User data loading from auth system
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        if (data.success && data.profile) {
            // Merge with existing profileData and store
            profileData = { ...profileData, ...data.profile };
            localStorage.setItem('mediassist-profile', JSON.stringify(profileData));
            // Update UI with new profile data
            updateProfileUI();
        }
    } catch (error) {
        console.error('Failed to load user profile:', error);
    }
}

function loadUserData() {
    const user = localStorage.getItem('mediassist_user') || sessionStorage.getItem('mediassist_user');
    if (user) {
        try {
            const userData = JSON.parse(user);
            // Update profile data with auth user data
            if (userData.name) {
                profileData.name = userData.name;
            }
            if (userData.email) {
                profileData.email = userData.email;
            }
            if (userData.first_name) {
                profileData.name = `${userData.first_name} ${userData.last_name || ''}`.trim();
            }
            // Save updated profile data to localStorage
            localStorage.setItem("mediassist-profile", JSON.stringify(profileData));
            
            // Load user-specific data from backend
            loadUserMedicines();
            loadUserReminders();
            loadUserReports();
        } catch (e) {
            console.error("Failed to load user data", e);
        }
    }
}

// Load user medicines from backend
async function loadUserMedicines() {
    try {
        const response = await fetch('/api/medicines');
        const data = await response.json();
        if (data.success) {
            medicines = data.medicines;
            localStorage.setItem('mediassist-medicines', JSON.stringify(medicines));
        }
    } catch (error) {
        console.error('Failed to load medicines:', error);
        // Fallback to localStorage
        const saved = localStorage.getItem('mediassist-medicines');
        if (saved) {
            medicines = JSON.parse(saved);
        }
    }
}

// Load user reminders from backend
async function loadUserReminders() {
    try {
        const response = await fetch('/api/reminders');
        const data = await response.json();
        if (data.success) {
            reminders = data.reminders;
            localStorage.setItem('mediassist-reminders', JSON.stringify(reminders));
        }
    } catch (error) {
        console.error('Failed to load reminders:', error);
        // Fallback to localStorage
        const saved = localStorage.getItem('mediassist-reminders');
        if (saved) {
            reminders = JSON.parse(saved);
        }
    }
}

// Load user reports from backend
async function loadUserReports() {
    try {
        const response = await fetch('/api/reports');
        const data = await response.json();
        if (data.success) {
            reports = data.reports || [];
            localStorage.setItem('mediassist-reports', JSON.stringify(reports));
            if (typeof renderReportsList === 'function') renderReportsList();
        }
    } catch (error) {
        console.error('Failed to load reports:', error);
    }
}

// Profile section
function saveProfile() {
    // Update profileData from form fields
    profileData.name = document.getElementById("profile-name").value.trim();
    profileData.age = document.getElementById("profile-age").value;
    profileData.email = document.getElementById("profile-email").value.trim();
    profileData.phone = document.getElementById("profile-phone").value.trim();
    profileData.blood = document.getElementById("profile-blood").value;
    profileData.doctor = document.getElementById("profile-doctor").value.trim();
    profileData.conditions = document.getElementById("profile-conditions").value.trim();
    profileData.allergies = document.getElementById("profile-allergies").value.trim();

    // Save to localStorage
    localStorage.setItem("mediassist-profile", JSON.stringify(profileData));
    // Send to backend
    fetch('/api/user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile: profileData })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast("✅ Profile saved to server");
        } else {
            showToast(`❌ Failed to save profile: ${data.message}`);
        }
    })
    .catch(err => {
        console.error('Error saving profile:', err);
        showToast('❌ Error saving profile to server');
    });

    // Update UI
    updateProfileUI();
    showToast("✅ Profile saved locally");
}

function loadProfileData() {
    const saved = localStorage.getItem("mediassist-profile");
    if (saved) {
        try {
            profileData = JSON.parse(saved);
        } catch (e) {
            console.error("Failed to load profile data", e);
        }
    }
    updateProfileUI();
}

function updateProfileUI() {
    // Update header
    const headerAvatar = document.getElementById("header-avatar");
    const headerUsername = document.getElementById("header-username");
    if (headerAvatar) headerAvatar.textContent = profileData.name.charAt(0).toUpperCase();
    if (headerUsername) headerUsername.textContent = profileData.name;

    // Update dashboard welcome greeting
    const welcomeTitle = document.getElementById("welcome-title");
    if (welcomeTitle && profileData.name && profileData.name !== "User") {
        welcomeTitle.textContent = `Hi, ${profileData.name.split(' ')[0]}! 👋`;
    }

    // Update chat introduction with the actual user name if available
    updateChatIntro();

    // Update profile page display
    const profileAvatar = document.getElementById("profile-avatar");
    const profileDisplayName = document.getElementById("profile-display-name");
    const profileDisplayEmail = document.getElementById("profile-display-email");
    const profileMedCount = document.getElementById("profile-med-count");

    if (profileAvatar) profileAvatar.textContent = profileData.name.charAt(0).toUpperCase();
    if (profileDisplayName) profileDisplayName.textContent = profileData.name;
    if (profileDisplayEmail) profileDisplayEmail.textContent = profileData.email;
    if (profileMedCount) profileMedCount.textContent = `${medicines.length} Medicines`;

    // Update form fields
    const profileName = document.getElementById("profile-name");
    const profileAge = document.getElementById("profile-age");
    const profileEmail = document.getElementById("profile-email");
    const profilePhone = document.getElementById("profile-phone");
    const profileBlood = document.getElementById("profile-blood");
    const profileDoctor = document.getElementById("profile-doctor");
    const profileConditions = document.getElementById("profile-conditions");
    const profileAllergies = document.getElementById("profile-allergies");

    if (profileName) profileName.value = profileData.name;
    if (profileAge) profileAge.value = profileData.age;
    if (profileEmail) profileEmail.value = profileData.email;

    // Refresh chat intro if profileData changed
    updateChatIntro();
    if (profilePhone) profilePhone.value = profileData.phone;
    if (profileBlood) profileBlood.value = profileData.blood;
    if (profileDoctor) profileDoctor.value = profileData.doctor;
    if (profileConditions) profileConditions.value = profileData.conditions;
    if (profileAllergies) profileAllergies.value = profileData.allergies;
}

function updateChatIntro() {
    const intro = document.getElementById("chat-intro-text");
    if (!intro) return;

    const firstName = profileData.name && profileData.name !== "User"
        ? profileData.name.split(" ")[0]
        : "";

    if (firstName) {
        intro.innerHTML = `👋 Hello ${escapeHtml(firstName)}! I'm your personal medicine assistant.<br><br>Ask me about any medicine — dosage, uses, side effects, precautions, or reminders. I'm here to help!`;
    } else {
        intro.innerHTML = `👋 Hello! I'm your personal medicine assistant.<br><br>Ask me about any medicine — dosage, uses, side effects, precautions, or reminders. I'm here to help!`;
    }
}

// Prescription upload (drag & drop and file picker)
function handleDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer?.files[0];
    if (file) processFile(file);
}

function handleFileUpload(e) {
    const file = e.target?.files[0];
    if (file) processFile(file);
}

async function processFile(file) {
    const preview = document.getElementById("upload-preview");
    if (!preview) return;

    preview.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-top:14px;padding:12px;background:var(--bg-card);border-radius:10px; border:1px solid var(--border-color);">
        <i class="fa-solid fa-spinner fa-spin" style="color:var(--primary);font-size:20px;"></i>
        <div>
            <strong style="font-size:13px;color:var(--text-primary)">Analyzing ${file.name}...</strong>
            <p style="font-size:11px;color:var(--text-muted)">Please wait, extracting medicines.</p>
        </div>
    </div>`;

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/api/reports/upload-prescription", {
            method: "POST",
            body: formData
        });
        const data = await response.json();

        if (data.success) {
            const parsedCount = data.medicines ? data.medicines.length : 0;
            preview.innerHTML = `
            <div style="display:flex;align-items:center;gap:10px;margin-top:14px;padding:12px;background:var(--success-light);border-radius:10px;">
                <i class="fa-solid fa-file-circle-check" style="color:var(--success);font-size:20px;"></i>
                <div>
                    <strong style="font-size:13px;color:var(--text-primary)">${file.name}</strong>
                    <p style="font-size:11px;color:var(--text-muted)">${data.message || (parsedCount + ' medicines parsed')}</p>
                </div>
            </div>`;
            showToast("✅ Prescription uploaded");

            // Always refresh reports list (report entry saved on server)
            await loadUserReports();

            // Always refresh medicines + reminders so Reminders page stays in sync
            await loadUserMedicines();
            await loadUserReminders();

            // Always update all UI components that depend on medicines/reminders
            if (typeof renderMedicinesTable === 'function') renderMedicinesTable();
            if (typeof renderReminderList === 'function') renderReminderList();
            if (typeof renderSchedule === 'function') renderSchedule();
            if (typeof updateDashboardStats === 'function') updateDashboardStats();
            updateProfileUI();

            if (parsedCount > 0 && data.reminders_created && data.reminders_created > 0) {
                showToast(`🔔 ${data.reminders_created} reminder(s) auto-created for parsed medicines`);
            }
        } else {
            throw new Error(data.message || "Upload failed");
        }
    } catch (error) {
        console.error("Upload error:", error);
        preview.innerHTML = `
        <div style="display:flex;align-items:center;gap:10px;margin-top:14px;padding:12px;background:var(--danger-light);border-radius:10px;">
            <i class="fa-solid fa-circle-exclamation" style="color:var(--danger);font-size:20px;"></i>
            <div>
                <strong style="font-size:13px;color:var(--text-primary)">Error uploading ${file.name}</strong>
                <p style="font-size:11px;color:var(--text-muted)">${error.message}</p>
            </div>
        </div>`;
        showToast("❌ Upload failed");
    }
}
