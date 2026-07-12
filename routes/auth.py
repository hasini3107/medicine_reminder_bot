# ============================================================
# routes/auth.py
#
# Responsibility: Handle authentication routes (login, register, logout)
# ============================================================

from flask import Blueprint, render_template, request, jsonify, session, redirect
import hashlib
import json
import os
import re
import requests
import secrets
import config

auth_bp = Blueprint("auth", __name__)

# Profile data file
PROFILE_FILE = "data/user_profiles.json"


# ------------------------------------------------------------------
# Helper functions for profile data
# ------------------------------------------------------------------
def _load_profiles():
    """Load user profiles from JSON file."""
    if not os.path.exists(PROFILE_FILE):
        return {}

    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_profiles(profiles):
    """Save user profiles to JSON file."""
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2)
    except Exception as exc:
        print(f"[ERROR] Failed to save profiles: {exc}")


def _hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC and a random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"


def _verify_password(stored_hash: str, password: str) -> bool:
    """Verify a password against a stored hash."""
    if not stored_hash or not password:
        return False

    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, digest_hex = stored_hash.split("$")
            salt = bytes.fromhex(salt_hex)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                int(iterations),
            )
            return digest.hex() == digest_hex
        except ValueError:
            return False

    return stored_hash == password


def _get_or_create_profile(email, name, password=None):
    """Get existing profile or create a new one."""
    profiles = _load_profiles()

    if email in profiles:
        return profiles[email]

    new_profile = {
        "name": name,
        "email": email,
        "age": "",
        "phone": "",
        "blood": "B+",
        "doctor": "",
        "conditions": "",
        "allergies": "",
    }
    if password:
        new_profile["password_hash"] = _hash_password(password)

    profiles[email] = new_profile
    _save_profiles(profiles)

    return new_profile


def _validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))


# ------------------------------------------------------------------
# GET /login - Render login page
# ------------------------------------------------------------------
@auth_bp.route("/login")
def login():
    """Render the login page."""
    return render_template("pages/login.html")


# ------------------------------------------------------------------
# GET /register - Render registration page
# ------------------------------------------------------------------
@auth_bp.route("/register")
def register():
    """Render the registration page."""
    return render_template("pages/register.html")



# ------------------------------------------------------------------
# GET /mock-google-login - Render Google account chooser mockup
# ------------------------------------------------------------------
@auth_bp.route("/mock-google-login")
def mock_google_login():
    """Render the mock Google Sign-In popup page."""
    return render_template("pages/google_chooser.html")


# ------------------------------------------------------------------
# POST /api/auth/login - Handle login API
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    """Handle login API request."""
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({"success": False, "message": "Email and password are required"}), 400
        if not _validate_email(email):
            return jsonify({"success": False, "message": "Please enter a valid email address"}), 400

        profiles = _load_profiles()
        profile = profiles.get(email)
        if not profile:
            profile = _get_or_create_profile(email, email.split("@")[0].capitalize(), password)
            profiles = _load_profiles()
            profile = profiles.get(email)

        stored_hash = profile.get("password_hash") or profile.get("password")
        if not _verify_password(stored_hash, password):
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

        user_name = profile.get("name") or email.split("@")[0].capitalize()
        user = {
            "id": 1,
            "email": email,
            "name": user_name,
            "first_name": user_name.split()[0] if " " in user_name else user_name,
            "last_name": "User",
        }
        user["profile"] = profile

        session["user_id"] = user["id"]
        session["user_email"] = user["email"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user,
        })

    except Exception as exc:
        print(f"[ERROR] Login failed: {exc}")
        return jsonify({"success": False, "message": "Login failed"}), 500


# ------------------------------------------------------------------
# POST /api/auth/register - Handle registration API
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    """Handle registration API request."""
    try:
        data = request.get_json(silent=True) or {}
        first_name = str(data.get("first_name", "")).strip()
        last_name = str(data.get("last_name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not all([first_name, last_name, email, password]):
            return jsonify({"success": False, "message": "All fields are required"}), 400
        if len(password) < 8:
            return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400
        if not _validate_email(email):
            return jsonify({"success": False, "message": "Please enter a valid email address"}), 400

        profiles = _load_profiles()
        if email in profiles:
            return jsonify({"success": False, "message": "This email is already registered"}), 409

        full_name = f"{first_name} {last_name}"
        profile = _get_or_create_profile(email, full_name, password)
        user = {
            "id": 1,
            "email": email,
            "name": full_name,
            "first_name": first_name,
            "last_name": last_name,
        }
        user["profile"] = profile

        session["user_id"] = user["id"]
        session["user_email"] = user["email"]

        return jsonify({
            "success": True,
            "message": "Registration successful",
            "user": user,
        })

    except Exception as exc:
        print(f"[ERROR] Registration failed: {exc}")
        return jsonify({"success": False, "message": "Registration failed"}), 500



# ------------------------------------------------------------------
# POST /api/auth/social - Handle Social Login/Register (Google/Apple)
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/social", methods=["POST"])
def api_social_auth():
    """Handle social auth (Google/Apple) login & registration."""
    try:
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        name = str(data.get("name", "")).strip()
        provider = str(data.get("provider", "google")).strip()

        if not email or not name:
            return jsonify({"success": False, "message": "Email and Name are required"}), 400

        profile = _get_or_create_profile(email, name, secrets.token_hex(16))
        
        user_name = profile.get("name") or name
        user = {
            "id": 999,
            "email": email,
            "name": user_name,
            "first_name": user_name.split()[0] if " " in user_name else user_name,
            "last_name": user_name.split()[1] if " " in user_name and len(user_name.split()) > 1 else "User",
        }
        user["profile"] = profile

        session["user_id"] = user["id"]
        session["user_email"] = user["email"]

        return jsonify({
            "success": True,
            "message": f"Authenticated via {provider.capitalize()} successfully",
            "user": user,
        })
    except Exception as exc:
        print(f"[ERROR] Social auth failed: {exc}")
        return jsonify({"success": False, "message": "Social authentication failed"}), 500



# ------------------------------------------------------------------
# GET /api/auth/google/login - Redirect to Google Accounts login
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/google/login")
def google_login():
    """Disabled.

    This endpoint used to start Google OAuth login.
    It is intentionally blocked so the "Continue with Google" functionality
    cannot be triggered (even via direct URL).
    """
    return (
        "Google login is disabled for this deployment.",
        403,
        {"Content-Type": "text/plain; charset=utf-8"},
    )



# ------------------------------------------------------------------
# GET /api/auth/google/callback - Handle Redirect from Google
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/google/callback")
def google_callback():
    """Handle callback from Google's OAuth server."""
    code = request.args.get("code")
    if not code:
        return "Authentication code missing from Google", 400

    base_url = (getattr(config, "GOOGLE_REDIRECT_BASE_URL", "") or "").strip()
    if not base_url:
        base_url = request.host_url.rstrip('/')

    redirect_uri = base_url + "/api/auth/google/callback"
    print(f"[MediAssist] Google callback redirect_uri: {redirect_uri}")
    
    try:
        # Exchange authorization code for token
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15
        )
        token_data = token_response.json()
        if "error" in token_data:
            return f"Error exchanging token: {token_data.get('error_description')}", 400
            
        id_token = token_data.get("id_token")
        
        # Get user details from Google token info endpoint
        tokeninfo_response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=10
        )
        user_info = tokeninfo_response.json()
        if "error" in user_info:
            return f"Failed to verify token: {user_info.get('error_description')}", 400
            
        email = user_info.get("email")
        name = user_info.get("name") or email.split("@")[0].capitalize()
        
        # Log in or register the Google user profile
        profile = _get_or_create_profile(email, name, secrets.token_hex(16))
        
        # Initialize flask session
        session["user_id"] = 999
        session["user_email"] = email
        
        # Temporarily store user data in session to be picked up by dashboard
        session["google_login_user"] = {
            "id": 999,
            "email": email,
            "name": name,
            "first_name": user_info.get("given_name") or name.split()[0],
            "last_name": user_info.get("family_name") or "User"
        }
        
        from flask import redirect
        return redirect("/#google-success")
        
    except Exception as e:
        print(f"[ERROR] Google OAuth Callback failed: {e}")
        return f"Authentication failed: {str(e)}", 500


# ------------------------------------------------------------------
# GET /api/auth/google/session - Fetch Google user info client-side
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/google/session")
def google_session():
    """Retrieve Google user login info to store client-side."""
    user = session.pop("google_login_user", None)
    if user:
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "No active google login session"}), 404


# ------------------------------------------------------------------
# POST /api/auth/google/save-config - Temporary Credentials Savior
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/google/save-config", methods=["POST"])
def google_save_config():
    """Save Google OAuth credentials dynamically (valid until restart)."""
    try:
        data = request.get_json(silent=True) or {}
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        
        if not client_id or not client_secret:
            return jsonify({"success": False, "message": "Client ID and Client Secret are required"}), 400
            
        # Dynamically set config values
        config.GOOGLE_CLIENT_ID = client_id
        config.GOOGLE_CLIENT_SECRET = client_secret
        
        return jsonify({"success": True, "message": "Configuration saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ------------------------------------------------------------------
# POST /api/auth/logout - Handle logout API
# ------------------------------------------------------------------
@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """Handle logout API request."""
    try:
        session.clear()
        return jsonify({"success": True, "message": "Logout successful"})
    except Exception as exc:
        print(f"[ERROR] Logout failed: {exc}")
        return jsonify({"success": False, "message": "Logout failed"}), 500
