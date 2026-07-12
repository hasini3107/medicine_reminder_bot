# ============================================================
# routes/data.py
#
# Responsibility: Handle user-specific data APIs (medicines, reminders, reports)
# ============================================================

from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import json
import os
from datetime import datetime

from config import UPLOAD_EXTENSIONS

data_bp = Blueprint("data", __name__)

# Data files
MEDICINES_FILE = "data/user_medicines.json"
REMINDERS_FILE = "data/user_reminders.json"
REPORTS_FILE = "data/user_reports.json"


# ------------------------------------------------------------------
# Helper functions for data storage
# ------------------------------------------------------------------
def _load_data(file_path):
    """Load user data from JSON file."""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def _save_data(file_path, data):
    """Save user data to JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save data: {e}")


def _save_report_entry(user_email, filename, filepath):
    """Save a report entry for uploaded prescription files."""
    reports_data = _load_data(REPORTS_FILE)
    if user_email not in reports_data:
        reports_data[user_email] = []
    new_id = max([r.get("id", 0) for r in reports_data[user_email]], default=0) + 1
    report = {
        "id": new_id,
        "filename": filename,
        "filepath": filepath,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    reports_data[user_email].append(report)
    _save_data(REPORTS_FILE, reports_data)
    return report


def _get_user_email():
    """Get current user email from session."""
    return session.get("user_email", "")


def _add_default_reminders(user_email: str, medicines_list: list):
    """Create simple default reminders for newly added medicines.
    Each reminder will be at 09:00 by default and marked pending.
    Returns the list of created reminders.
    """
    if not medicines_list:
        return []

    reminders_data = _load_data(REMINDERS_FILE)
    user_reminders = reminders_data.get(user_email, [])
    current_max = max([r.get("id", 0) for r in user_reminders]) if user_reminders else 0
    created = []
    for med in medicines_list:
        current_max += 1
        reminder = {
            "id": current_max,
            "medId": med.get("id"),
            "medName": med.get("name") or med.get("Medicine Name") or "",
            "time": "09:00",
            "done": False,
            "notes": "Auto-created reminder from prescription upload"
        }
        user_reminders.append(reminder)
        created.append(reminder)

    reminders_data[user_email] = user_reminders
    _save_data(REMINDERS_FILE, reminders_data)
    return created


# ------------------------------------------------------------------
# Medicines APIs
# ------------------------------------------------------------------
@data_bp.route("/api/medicines", methods=["GET"])
def get_medicines():
    """Get medicines for current user (or guest)."""
    user_email = _get_user_email() or "guest"
    medicines_data = _load_data(MEDICINES_FILE)
    user_medicines = medicines_data.get(user_email, [])
    return jsonify({"success": True, "medicines": user_medicines})


@data_bp.route("/api/medicines", methods=["POST"])
def save_medicines():
    """Save medicines for current user (or guest)."""
    user_email = _get_user_email() or "guest"
    try:
        data = request.get_json()
        medicines = data.get("medicines", [])
        medicines_data = _load_data(MEDICINES_FILE)
        medicines_data[user_email] = medicines
        _save_data(MEDICINES_FILE, medicines_data)
        # Auto-create default reminders for medicines that don't have one yet
        try:
            reminders_data = _load_data(REMINDERS_FILE)
            user_reminders = reminders_data.get(user_email, [])
            existing_med_ids = {r.get('medId') for r in user_reminders}
            to_create = [m for m in medicines if m.get('id') and m.get('id') not in existing_med_ids]
            created = []
            if to_create:
                created = _add_default_reminders(user_email, to_create)
        except Exception:
            created = []

        return jsonify({"success": True, "message": "Medicines saved", "reminders_created": len(created)})
    except Exception as e:
        print(f"[ERROR] Failed to save medicines: {e}")
        return jsonify({"success": False, "message": "Failed to save medicines"}), 500


# ------------------------------------------------------------------
# Reminders APIs
# ------------------------------------------------------------------
@data_bp.route("/api/reminders", methods=["GET"])
def get_reminders():
    """Get reminders for current user (or guest)."""
    user_email = _get_user_email() or "guest"
    reminders_data = _load_data(REMINDERS_FILE)
    user_reminders = reminders_data.get(user_email, [])
    return jsonify({"success": True, "reminders": user_reminders})


@data_bp.route("/api/reminders", methods=["POST"])
def save_reminders():
    """Save reminders for current user (or guest)."""
    user_email = _get_user_email() or "guest"
    try:
        data = request.get_json()
        reminders = data.get("reminders", [])
        reminders_data = _load_data(REMINDERS_FILE)
        reminders_data[user_email] = reminders
        _save_data(REMINDERS_FILE, reminders_data)
        return jsonify({"success": True, "message": "Reminders saved"})
    except Exception as e:
        print(f"[ERROR] Failed to save reminders: {e}")
        return jsonify({"success": False, "message": "Failed to save reminders"}), 500

# ------------------------------------------------------------------
# User Profile APIs
# ------------------------------------------------------------------
# User Profile APIs
@data_bp.route("/api/user", methods=["GET"])
def get_user_profile():
    """Get user profile for current user or guest."""
    user_email = _get_user_email()
    if not user_email:
        user_email = "guest"
    profiles_path = "data/user_profiles.json"
    profiles = _load_data(profiles_path)
    profile = profiles.get(user_email, {})
    return jsonify({"success": True, "profile": profile})

@data_bp.route("/api/user", methods=["POST"])
def save_user_profile():
    """Save user profile for current user or guest."""
    user_email = _get_user_email()
    if not user_email:
        user_email = "guest"
    try:
        data = request.get_json()
        profile = data.get("profile", {})
        profiles_path = "data/user_profiles.json"
        profiles = _load_data(profiles_path)
        profiles[user_email] = profile
        _save_data(profiles_path, profiles)
        return jsonify({"success": True, "message": "Profile saved"})
    except Exception as e:
        print(f"[ERROR] Failed to save user profile: {e}")
        return jsonify({"success": False, "message": "Failed to save profile"}), 500



# ------------------------------------------------------------------
# Reports APIs
# ------------------------------------------------------------------
@data_bp.route("/api/reports", methods=["GET"])
def get_reports():
    """Get reports for current user (or guest)."""
    user_email = _get_user_email() or "guest"
    reports_data = _load_data(REPORTS_FILE)
    user_reports = reports_data.get(user_email, [])
    return jsonify({"success": True, "reports": user_reports})


@data_bp.route("/api/reports", methods=["POST"])
def save_report():
    """Save report for current user."""
    user_email = _get_user_email()
    if not user_email:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        report = data.get("report", {})
        
        reports_data = _load_data(REPORTS_FILE)
        if user_email not in reports_data:
            reports_data[user_email] = []
        
        reports_data[user_email].append(report)
        _save_data(REPORTS_FILE, reports_data)
        
        return jsonify({"success": True, "message": "Report saved"})
    except Exception as e:
        print(f"[ERROR] Failed to save report: {e}")
        return jsonify({"success": False, "message": "Failed to save report"}), 500


@data_bp.route("/api/reports/upload", methods=["POST"])
def upload_report():
    """Handle report file upload."""
    user_email = _get_user_email()
    if not user_email:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in UPLOAD_EXTENSIONS:
            return jsonify({"success": False, "message": "Unsupported file type"}), 400
        
        upload_dir = "uploads/reports"
        os.makedirs(upload_dir, exist_ok=True)
        
        safe_name = secure_filename(file.filename)
        filename = f"{user_email}_{os.path.splitext(safe_name)[0]}{ext}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Create report entry
        reports_data = _load_data(REPORTS_FILE)
        if user_email not in reports_data:
            reports_data[user_email] = []
        new_id = max([r.get("id", 0) for r in reports_data[user_email]], default=0) + 1
        report = {
            "id": new_id,
            "filename": file.filename,
            "filepath": filepath,
            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        reports_data[user_email].append(report)
        _save_data(REPORTS_FILE, reports_data)
        
        return jsonify({"success": True, "message": "Report uploaded successfully", "report": report})
    except Exception as e:
        print(f"[ERROR] Failed to upload report: {e}")
        return jsonify({"success": False, "message": "Failed to upload report"}), 500


@data_bp.route("/api/reports/upload-prescription", methods=["POST"])
def upload_prescription():
    """Handle prescription file upload, extract text, parse medicines, and save to user's medicines."""
    from utils.ocr_helper import extract_text_from_file
    from utils.prescription_parser import parse_prescription_text
    
    user_email = _get_user_email()
    if not user_email:
        user_email = "guest"
        
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file provided"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in UPLOAD_EXTENSIONS:
            return jsonify({"success": False, "message": "Unsupported file type"}), 400
            
        upload_dir = "uploads/prescriptions"
        os.makedirs(upload_dir, exist_ok=True)
        
        safe_name = secure_filename(file.filename)
        filepath = os.path.join(upload_dir, f"{user_email}_{safe_name}")
        file.save(filepath)
        _save_report_entry(user_email, file.filename, filepath)

        new_medicines = []
        try:
            # 1. Extract Text
            extracted_text = extract_text_from_file(filepath)
            
            # 2. Parse Text to Medicines using Ollama
            new_medicines = parse_prescription_text(extracted_text)

            # 3. Save to user's medicines
            if new_medicines:
                medicines_data = _load_data(MEDICINES_FILE)
                user_medicines = medicines_data.get(user_email, [])
                
                # assign IDs
                current_max_id = max([m.get("id", 0) for m in user_medicines]) if user_medicines else 0
                saved_meds = []
                for med in new_medicines:
                    current_max_id += 1
                    med["id"] = current_max_id
                    # ensure default values if missing
                    med.setdefault("status", "Active")
                    user_medicines.append(med)
                    saved_meds.append(med)
                    
                medicines_data[user_email] = user_medicines
                _save_data(MEDICINES_FILE, medicines_data)
                # Create default reminders for saved medicines
                created_reminders = _add_default_reminders(user_email, saved_meds)

            return jsonify({
                "success": True,
                "medicines": new_medicines,
                "reminders_created": len(created_reminders) if new_medicines else 0,
                "message": "Prescription uploaded successfully." if new_medicines else "Prescription uploaded and saved, but no medicines were parsed. Install Tesseract and try again to extract details."
            })
        except FileNotFoundError as e:
            print(f"[ERROR] Tesseract OCR missing: {e}")
            return jsonify({
                "success": True,
                "medicines": [],
                "message": "Prescription saved, but OCR is not installed or not found. Install Tesseract and set TESSERACT_CMD or add tesseract to your PATH to parse medicine details."
            })
        except Exception as e:
            print(f"[ERROR] Failed to process prescription: {e}")
            return jsonify({
                "success": True,
                "medicines": [],
                "message": "Prescription saved, but parsing failed. Please check the OCR and Ollama services or try again later."
            })
    except Exception as e:
        print(f"[ERROR] upload_prescription failed: {e}")
        return jsonify({"success": False, "message": "Failed to upload prescription"}), 500


@data_bp.route("/api/reports/parse-report", methods=["POST"])
def parse_saved_report():
    """Re-run OCR and parsing on a previously uploaded report.
    Accepts JSON: { "report_id": <id> } or { "filename": "name.png" } and returns parsed medicines.
    """
    from utils.ocr_helper import extract_text_from_file
    from utils.prescription_parser import parse_prescription_text

    user_email = _get_user_email() or "guest"
    try:
        data = request.get_json() or {}
        report_id = data.get("report_id")
        filename = data.get("filename")

        reports_data = _load_data(REPORTS_FILE)
        user_reports = reports_data.get(user_email, [])

        target = None
        if report_id is not None:
            for r in user_reports:
                if r.get("id") == int(report_id):
                    target = r
                    break
        elif filename:
            for r in user_reports:
                if r.get("filename") == filename:
                    target = r
                    break

        if not target:
            return jsonify({"success": False, "message": "Report not found"}), 404

        filepath = target.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Report file not found on server"}), 404

        extracted_text = extract_text_from_file(filepath)
        new_medicines = parse_prescription_text(extracted_text)

        # Save medicines if any
        saved = []
        if new_medicines:
            medicines_data = _load_data(MEDICINES_FILE)
            user_medicines = medicines_data.get(user_email, [])
            current_max_id = max([m.get("id", 0) for m in user_medicines]) if user_medicines else 0
            for med in new_medicines:
                current_max_id += 1
                med["id"] = current_max_id
                med.setdefault("status", "Active")
                user_medicines.append(med)
                saved.append(med)
            medicines_data[user_email] = user_medicines
            _save_data(MEDICINES_FILE, medicines_data)
            # Create default reminders for saved medicines
            created_reminders = _add_default_reminders(user_email, saved)

        return jsonify({"success": True, "medicines": saved, "reminders_created": len(created_reminders) if new_medicines else 0, "message": "Parsed and saved medicines"})
    except Exception as e:
        print(f"[ERROR] parse_saved_report failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@data_bp.route("/api/reports/ocr-text", methods=["POST"])
def get_report_ocr_text():
    """Return the OCR-extracted text for a previously uploaded report.
    Accepts JSON: { "report_id": <id> } or { "filename": "name.png" }
    """
    from utils.ocr_helper import extract_text_from_file

    user_email = _get_user_email() or "guest"
    try:
        data = request.get_json() or {}
        report_id = data.get("report_id")
        filename = data.get("filename")

        reports_data = _load_data(REPORTS_FILE)
        user_reports = reports_data.get(user_email, [])

        target = None
        if report_id is not None:
            for r in user_reports:
                if r.get("id") == int(report_id):
                    target = r
                    break
        elif filename:
            for r in user_reports:
                if r.get("filename") == filename:
                    target = r
                    break

        if not target:
            return jsonify({"success": False, "message": "Report not found"}), 404

        filepath = target.get("filepath")
        if not filepath or not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Report file not found on server"}), 404

        extracted_text = extract_text_from_file(filepath)
        return jsonify({"success": True, "text": extracted_text})
    except Exception as e:
        print(f"[ERROR] get_report_ocr_text failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

