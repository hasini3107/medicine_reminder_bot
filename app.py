# ============================================================
# app.py — MediAssist Flask Entry Point
#
# This file only:
#   1. Creates the Flask app.
#   2. Registers blueprints (routes).
#   3. Starts the development server when run directly.
#
# All business logic lives in routes/ and utils/.
# All settings live in config.py.
# ============================================================

from flask import Flask
from flask_cors import CORS

from config import DEBUG, HOST, PORT, SECRET_KEY, MAX_CONTENT_LENGTH
from routes.main import main_bp
from routes.chat import chat_bp
from routes.auth import auth_bp
from routes.data import data_bp


def create_app() -> Flask:
    """Application factory — create and configure the Flask app."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    CORS(app)

    # Register blueprints
    app.register_blueprint(main_bp)   # GET  /
    app.register_blueprint(chat_bp)   # POST /chat
    app.register_blueprint(auth_bp)   # Auth routes
    app.register_blueprint(data_bp)   # User data APIs

    # Serve uploaded files (prescriptions & reports) so the "View" link works
    import os
    from flask import send_from_directory

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        uploads_dir = os.path.join(app.root_path, "uploads")
        return send_from_directory(uploads_dir, filename)

    return app


# ---- Run directly ------------------------------------------------
if __name__ == "__main__":
    try:
        app = create_app()
        print(f"Starting Flask server on {HOST}:{PORT}")
        app.run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()