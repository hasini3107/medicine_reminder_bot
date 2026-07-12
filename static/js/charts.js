// ============================================================
// static/js/charts.js
//
// Responsibilities:
//   - Draw the donut (ring) chart on a <canvas> element.
//   - Draw the weekly bar chart in the Reports page.
//   - Handle the "This Week / This Month" toggle on the dashboard.
// ============================================================


// ------------------------------------------------------------------
// Donut chart
// ------------------------------------------------------------------
/**
 * Draw a ring/donut chart showing taken / pending / missed ratios.
 *
 * @param {string} canvasId  - id of the <canvas> element to draw on.
 * @param {number} taken     - Number of doses taken.
 * @param {number} pending   - Number of doses pending.
 * @param {number} missed    - Number of doses missed.
 */
function drawDonut(canvasId, taken, pending, missed) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx   = canvas.getContext("2d");
    const W     = canvas.width;
    const H     = canvas.height;
    const cx    = W / 2;
    const cy    = H / 2;
    const r     = Math.min(W, H) / 2 - 12;
    const inner = r * 0.62;           // inner radius (the "hole")

    const total  = taken + pending + missed || 1;
    const slices = [
        { val: taken,   color: "#2ec4b6" },   // teal  — taken
        { val: pending, color: "#f77f00" },   // orange — pending
        { val: missed,  color: "#e63946" },   // red    — missed
    ];

    ctx.clearRect(0, 0, W, H);

    // Draw outer slices
    let startAngle = -Math.PI / 2;
    slices.forEach(({ val, color }) => {
        const sweep = (val / total) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, r, startAngle, startAngle + sweep);
        ctx.closePath();
        ctx.fillStyle = color;
        ctx.fill();
        startAngle += sweep;
    });

    // Punch out the inner circle to create the donut hole
    // Use the CSS variable for the card background so it adapts to dark mode
    const cardBg = getComputedStyle(document.documentElement)
        .getPropertyValue("--card-bg")
        .trim() || "#ffffff";

    ctx.beginPath();
    ctx.arc(cx, cy, inner, 0, Math.PI * 2);
    ctx.fillStyle = cardBg;
    ctx.fill();
}


// ------------------------------------------------------------------
// Overview period toggle (dashboard card)
// ------------------------------------------------------------------
/**
 * Called when the user changes the "This Week / This Month" selector
 * on the Medicine Intake Overview card.
 */
function updateChart() {
    const taken   = reminders.filter(r => r.done).length;
    const pending = reminders.filter(r => !r.done).length;
    const missed  = 0;
    const total   = taken + pending + missed || 1;
    const pct     = Math.round((taken / total) * 100);

    drawDonut("intakeDonut", taken, pending, missed);
    document.getElementById("donut-pct").textContent    = `${pct}%`;
    document.getElementById("leg-taken").textContent    = `${taken} (${pct}%)`;
    document.getElementById("leg-pending").textContent  = `${pending} (${Math.round(pending/total*100)}%)`;
    document.getElementById("leg-missed").textContent   = `0 (0%)`;
}



// ------------------------------------------------------------------
// Bar chart (Reports page) — REMOVED
// Weekly Adherence and Medicine Distribution charts have been removed.
// ------------------------------------------------------------------
