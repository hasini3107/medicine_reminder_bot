// ============================================================
// static/js/reports.js
// Render reports list, re-parse, and export report as PDF.
// Depends on global `reports`, `medicines`, `reminders`, `profileData`
// and functions `showToast`, `escapeHtml`, `loadUserMedicines`, `loadUserReminders`.
// ============================================================

function renderReportsList() {
    const container = document.getElementById('reports-list');
    if (!container) return;

    container.innerHTML = '';
    if (!reports || reports.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:12px;">No uploads yet.</p>';
        return;
    }

    // show most recent first
    const items = [...reports].reverse();
    items.forEach(r => {
        const uploadedAt = r.uploaded_at || '';
        const rawPath = r.filepath || '';
        // Normalise Windows backslashes to forward-slashes for URL use
        const viewUrl = rawPath ? '/' + rawPath.replace(/\\/g, '/') : '#';
        const ext = (r.filename || '').split('.').pop().toLowerCase();
        const icon = ext === 'pdf' ? 'fa-file-pdf' : (ext === 'png' || ext === 'jpg' || ext === 'jpeg') ? 'fa-file-image' : 'fa-file-medical';
        const iconColor = ext === 'pdf' ? '#e63946' : '#4361ee';

        container.innerHTML += `
            <div class="report-row" style="display:flex;align-items:center;justify-content:space-between;padding:10px 8px;border-bottom:1px solid var(--border-color);gap:12px;">
                <div style="display:flex;align-items:center;gap:10px;min-width:0;">
                    <i class="fa-solid ${icon}" style="font-size:22px;color:${iconColor};flex-shrink:0;"></i>
                    <div style="min-width:0;">
                        <strong style="display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px;">${escapeHtml(r.filename || 'file')}</strong>
                        <div style="font-size:11px;color:var(--text-muted);">${escapeHtml(uploadedAt)}</div>
                    </div>
                </div>
                <div style="display:flex;gap:6px;align-items:center;flex-shrink:0;">
                    <button class="secondary-btn" style="font-size:12px;padding:4px 10px;" onclick="reparseReport('${encodeURIComponent(r.filename || '')}')"><i class="fa-solid fa-rotate"></i> Re-parse</button>
                    <a class="secondary-btn" style="font-size:12px;padding:4px 10px;text-decoration:none;" href="${viewUrl}" target="_blank"><i class="fa-solid fa-eye"></i> View</a>
                </div>
            </div>`;
    });
}

async function reparseReport(filename) {
    try {
        const decoded = decodeURIComponent(filename);
        const resp = await fetch('/api/reports/parse-report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ filename: decoded })
        });
        const data = await resp.json();
        if (data.success) {
            showToast('✅ Re-parse complete: ' + (data.medicines ? data.medicines.length : 0) + ' medicines found');
            // Refresh canonical data
            await loadUserMedicines();
            await loadUserReminders();
            if (typeof renderMedicinesTable === 'function') renderMedicinesTable();
            if (typeof renderReminderList === 'function') renderReminderList();
            if (typeof renderSchedule === 'function') renderSchedule();
            if (typeof updateDashboardStats === 'function') updateDashboardStats();
            // update reports from backend
            await loadUserReports();
        } else {
            showToast(`❌ Re-parse failed: ${data.message || 'unknown'}`, 'error');
        }
    } catch (e) {
        console.error('Re-parse error', e);
        showToast('❌ Re-parse error', 'error');
    }
}


// ------------------------------------------------------------------
// Export Report
// Builds a styled HTML report from live global state and opens the
// browser's Print / Save-as-PDF dialog in a new tab.
// ------------------------------------------------------------------
function exportReport() {
    const now          = new Date();
    const dateStr      = now.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    const timeStr      = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    const userName     = (typeof profileData !== 'undefined' && profileData.name) ? profileData.name : 'User';
    const totalMeds    = (typeof medicines !== 'undefined') ? medicines.length : 0;
    const activeMeds   = (typeof medicines !== 'undefined') ? medicines.filter(m => m.status === 'Active').length : 0;
    const takenCount   = (typeof reminders !== 'undefined') ? reminders.filter(r => r.done).length : 0;
    const pendingCount = (typeof reminders !== 'undefined') ? reminders.filter(r => !r.done).length : 0;
    const total        = takenCount + pendingCount || 1;
    const adherencePct = Math.round((takenCount / total) * 100);

    // ---- Medicines rows ----
    const medRows = (typeof medicines !== 'undefined' && medicines.length)
        ? medicines.map(m => `
            <tr>
                <td>${escapeHtml(m.name || '')}</td>
                <td>${escapeHtml(m.dosage || '—')}</td>
                <td>${escapeHtml(m.frequency || '—')}</td>
                <td><span class="badge ${m.status === 'Active' ? 'badge-active' : 'badge-inactive'}">${escapeHtml(m.status || '—')}</span></td>
            </tr>`).join('')
        : '<tr><td colspan="4" class="empty">No medicines added yet.</td></tr>';

    // ---- Reminders rows ----
    const reminderRows = (typeof reminders !== 'undefined' && reminders.length)
        ? reminders.map(r => `
            <tr>
                <td>${escapeHtml(r.medName || '')}</td>
                <td>${escapeHtml(r.time || '—')}</td>
                <td><span class="badge ${r.done ? 'badge-taken' : 'badge-pending'}">${r.done ? 'Taken' : 'Pending'}</span></td>
                <td>${escapeHtml(r.notes || '—')}</td>
            </tr>`).join('')
        : '<tr><td colspan="4" class="empty">No reminders set yet.</td></tr>';

    // ---- Uploaded prescriptions rows ----
    const uploadRows = (typeof reports !== 'undefined' && reports.length)
        ? [...reports].reverse().map(r => `
            <tr>
                <td>${escapeHtml(r.filename || '')}</td>
                <td>${escapeHtml(r.uploaded_at || '—')}</td>
            </tr>`).join('')
        : '<tr><td colspan="2" class="empty">No uploads yet.</td></tr>';

    const adherenceColor = adherencePct >= 70 ? '#2ec4b6' : adherencePct >= 40 ? '#f77f00' : '#e63946';

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>MediAssist Health Report — ${escapeHtml(userName)}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            color: #1a1a2e;
            background: #fff;
            padding: 40px;
            font-size: 13px;
        }
        /* ---- Header ---- */
        .rpt-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 3px solid #4361ee;
            padding-bottom: 20px;
            margin-bottom: 28px;
        }
        .rpt-header h1 { font-size: 26px; color: #4361ee; font-weight: 800; }
        .rpt-header p  { color: #666; margin-top: 5px; font-size: 12px; }
        .rpt-meta      { text-align: right; font-size: 12px; color: #555; line-height: 1.8; }
        .rpt-meta strong { color: #1a1a2e; font-size: 14px; }

        /* ---- Stats row ---- */
        .stats-row { display: flex; gap: 14px; margin-bottom: 30px; }
        .stat-box {
            flex: 1;
            background: #f0f4ff;
            border-radius: 10px;
            padding: 16px 10px;
            text-align: center;
        }
        .stat-box .num { font-size: 26px; font-weight: 800; color: #4361ee; }
        .stat-box .lbl { font-size: 11px; color: #666; margin-top: 4px; }

        /* ---- Sections ---- */
        section { margin-bottom: 32px; }
        h2 {
            font-size: 14px;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 10px;
            padding-left: 10px;
            border-left: 4px solid #4361ee;
        }

        /* ---- Tables ---- */
        table { width: 100%; border-collapse: collapse; }
        th {
            background: #4361ee;
            color: #fff;
            padding: 10px 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
        }
        td { padding: 9px 12px; border-bottom: 1px solid #e8ecf4; }
        tr:nth-child(even) td { background: #f8f9fd; }
        td.empty { text-align: center; color: #999; padding: 20px; }

        /* ---- Badges ---- */
        .badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-active   { background: #d1fae5; color: #065f46; }
        .badge-inactive { background: #fee2e2; color: #991b1b; }
        .badge-taken    { background: #d1fae5; color: #065f46; }
        .badge-pending  { background: #fff3cd; color: #92400e; }

        /* ---- Footer ---- */
        .rpt-footer {
            margin-top: 40px;
            border-top: 1px solid #e8ecf4;
            padding-top: 14px;
            font-size: 11px;
            color: #aaa;
            text-align: center;
        }

        @media print {
            body { padding: 20px; }
        }
    </style>
</head>
<body>
    <div class="rpt-header">
        <div>
            <h1>💊 MediAssist Health Report</h1>
            <p>Personal medicine adherence &amp; health summary</p>
        </div>
        <div class="rpt-meta">
            <strong>${escapeHtml(userName)}</strong><br/>
            ${dateStr}<br/>
            Generated at ${timeStr}
        </div>
    </div>

    <div class="stats-row">
        <div class="stat-box">
            <div class="num" style="color:#4361ee;">${totalMeds}</div>
            <div class="lbl">Total Medicines</div>
        </div>
        <div class="stat-box">
            <div class="num" style="color:#2ec4b6;">${activeMeds}</div>
            <div class="lbl">Active Medicines</div>
        </div>
        <div class="stat-box">
            <div class="num" style="color:#2ec4b6;">${takenCount}</div>
            <div class="lbl">Doses Taken</div>
        </div>
        <div class="stat-box">
            <div class="num" style="color:#f77f00;">${pendingCount}</div>
            <div class="lbl">Doses Pending</div>
        </div>
        <div class="stat-box">
            <div class="num" style="color:${adherenceColor};">${adherencePct}%</div>
            <div class="lbl">Adherence Rate</div>
        </div>
    </div>

    <section>
        <h2>My Medicines</h2>
        <table>
            <thead>
                <tr>
                    <th>Medicine Name</th>
                    <th>Dosage</th>
                    <th>Frequency</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>${medRows}</tbody>
        </table>
    </section>

    <section>
        <h2>Reminders</h2>
        <table>
            <thead>
                <tr>
                    <th>Medicine</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>${reminderRows}</tbody>
        </table>
    </section>

    <section>
        <h2>Uploaded Prescriptions</h2>
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Uploaded At</th>
                </tr>
            </thead>
            <tbody>${uploadRows}</tbody>
        </table>
    </section>

    <div class="rpt-footer">
        MediAssist &mdash; This report is for personal reference only. Always consult your doctor for medical advice.
    </div>

    <script>window.onload = function() { window.print(); };<\/script>
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url  = URL.createObjectURL(blob);
    const win  = window.open(url, '_blank');
    if (!win) {
        showToast('❌ Popup blocked — please allow popups for this site', 'error');
        return;
    }
    // Release the blob URL after the window has loaded and printed
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}
