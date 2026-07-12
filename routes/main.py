# ============================================================
# routes/main.py
#
# Responsibility: Serve the single-page MediAssist dashboard.
# ============================================================

from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Render the MediAssist dashboard (index.html)."""
    # Check if user is authenticated (for demo, always allow access)
    # In production, uncomment the following:
    # if "user_id" not in session:
    #     return redirect(url_for("auth.login"))
    return render_template("pages/index.html")
