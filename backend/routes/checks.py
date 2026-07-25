from flask import Blueprint, request, jsonify
from database import db
from models import EmployeeCheckLog, EmployeeLatestStatus
from datetime import datetime
import sys
import os
import json
import base64
import numpy as np
import cv2

# Path to the AI layer (for reusing PPEDetector, SafetyStatus)
_AI_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ai")
if _AI_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(_AI_DIR))

try:
    from ppe_detector import PPEDetector
    from safety_status import SafetyStatus
    _MODEL_PATH = os.path.join(os.path.abspath(_AI_DIR), "ppe_model_v8.pt")
    _detector   = PPEDetector(model_path=_MODEL_PATH)
    _safety     = SafetyStatus()
    _DETECT_READY = True
except Exception as _e:
    print(f"[checks] WARNING: Could not load PPEDetector for image upload: {_e}")
    _DETECT_READY = False

# Path to employee data
_EMPLOYEES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "employee_data", "employees.json"
)

def _load_employees():
    """Load employee list from employees.json."""
    try:
        with open(os.path.abspath(_EMPLOYEES_FILE), "r") as f:
            data = json.load(f)
        return data.get("employees", [])
    except Exception:
        return []

checks_bp = Blueprint("checks", __name__)

# Injected from app.py
socketio = None

def init_checks(sio):
    global socketio
    socketio = sio


# ── Receive check result from AI layer ────────────────────────────
@checks_bp.route("/api/report", methods=["POST"])
def receive_report():
    """
    AI layer calls this after every employee QR + PPE check.
    Stores full log + updates latest status table.
    Emits real-time update to dashboard.
    """
    data = request.json

    if not data:
        return jsonify({"error": "No data received"}), 400

    # ── Extract data ───────────────────────────────────────────────
    employee_id   = data.get("employee_id",   "UNKNOWN")
    employee_name = data.get("employee_name", "Unknown")
    department    = data.get("department",    "")
    role          = data.get("role",          "")
    has_helmet    = data.get("has_helmet",    False)
    has_vest      = data.get("has_vest",      False)
    has_gloves    = data.get("has_gloves",    False)
    has_goggles   = data.get("has_goggles",   False)
    has_boots     = data.get("has_boots",     False)
    missing_ppe   = ", ".join(data.get("missing_ppe", []))
    status        = data.get("status",        "NOT READY")
    camera_id     = data.get("camera_id",     "CAM-01")

    # ── Save to full history log ───────────────────────────────────
    log = EmployeeCheckLog(
        employee_id   = employee_id,
        employee_name = employee_name,
        department    = department,
        role          = role,
        has_helmet    = has_helmet,
        has_vest      = has_vest,
        has_gloves    = has_gloves,
        has_goggles   = has_goggles,
        has_boots     = has_boots,
        missing_ppe   = missing_ppe,
        status        = status,
        camera_id     = camera_id
    )
    db.session.add(log)

    # ── Update or create latest status for this employee ──────────
    existing = EmployeeLatestStatus.query.filter_by(
        employee_id=employee_id
    ).first()

    if existing:
        # Update existing row
        existing.employee_name = employee_name
        existing.department    = department
        existing.role          = role
        existing.has_helmet    = has_helmet
        existing.has_vest      = has_vest
        existing.has_gloves    = has_gloves
        existing.has_goggles   = has_goggles
        existing.has_boots     = has_boots
        existing.missing_ppe   = missing_ppe
        existing.status        = status
        existing.last_checked  = datetime.utcnow()
        existing.camera_id     = camera_id
    else:
        # Create new row
        latest = EmployeeLatestStatus(
            employee_id   = employee_id,
            employee_name = employee_name,
            department    = department,
            role          = role,
            has_helmet    = has_helmet,
            has_vest      = has_vest,
            has_gloves    = has_gloves,
            has_goggles   = has_goggles,
            has_boots     = has_boots,
            missing_ppe   = missing_ppe,
            status        = status,
            camera_id     = camera_id
        )
        db.session.add(latest)

    db.session.commit()

    # ── Emit real-time update to dashboard via WebSocket ──────────
    realtime_payload = {
        "employee_id":   employee_id,
        "employee_name": employee_name,
        "department":    department,
        "has_helmet":    has_helmet,
        "has_vest":      has_vest,
        "has_gloves":    has_gloves,
        "has_goggles":   has_goggles,
        "has_boots":     has_boots,
        "missing_ppe":   data.get("missing_ppe", []),
        "status":        status,
        "safety_percentage": data.get("safety_percentage", None),
        "track_id":          data.get("track_id", None),
        "camera_id":     camera_id,
        "timestamp":     datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    if socketio:
        socketio.emit("check_update", realtime_payload)
        print(f"[WebSocket] Emitted update → {employee_id} | {status}")

    print(f"[Checks] Saved → {employee_id} : {employee_name} | {status}")

    return jsonify({
        "status":  "received",
        "log_id":  log.id,
        "result":  status
    }), 200


# ── Get full check history ─────────────────────────────────────────
@checks_bp.route("/api/checks", methods=["GET"])
def get_checks():
    """Returns recent check history — used in logs table"""
    limit       = request.args.get("limit", 50, type=int)
    employee_id = request.args.get("employee_id", None)

    query = EmployeeCheckLog.query

    # Optional filter by employee
    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    logs = query.order_by(
        EmployeeCheckLog.timestamp.desc()
    ).limit(limit).all()

    return jsonify([l.to_dict() for l in logs])


# ── Get latest status of all employees ────────────────────────────
@checks_bp.route("/api/employees/status", methods=["GET"])
def get_all_employee_status():
    """
    Returns latest status for every employee.
    This is what powers the main dashboard table.
    """
    latest = EmployeeLatestStatus.query\
        .order_by(EmployeeLatestStatus.last_checked.desc())\
        .all()

    return jsonify([e.to_dict() for e in latest])


# ── Get single employee status ─────────────────────────────────────
@checks_bp.route("/api/employees/<employee_id>", methods=["GET"])
def get_employee(employee_id):
    """Returns current status + history for one employee"""
    latest = EmployeeLatestStatus.query.filter_by(
        employee_id=employee_id
    ).first()

    if not latest:
        return jsonify({"error": "Employee not found"}), 404

    # Get last 10 checks for this employee
    history = EmployeeCheckLog.query\
        .filter_by(employee_id=employee_id)\
        .order_by(EmployeeCheckLog.timestamp.desc())\
        .limit(10).all()

    return jsonify({
        "latest":  latest.to_dict(),
        "history": [h.to_dict() for h in history]
    })


# ── List all employees (for frontend dropdown) ────────────────────
@checks_bp.route("/api/employees/list", methods=["GET"])
def list_employees():
    """Returns the full employee roster from employees.json."""
    return jsonify(_load_employees())


# ── Image Upload PPE Detection ────────────────────────────────────
@checks_bp.route("/api/detect-image", methods=["POST"])
def detect_image():
    """
    Accepts a multipart image upload + optional employee_id.
    Runs the same PPE detection pipeline used for live camera frames:
      PPEDetector.detect() → check_ppe_compliance() → SafetyStatus.evaluate()
    Returns an annotated image (base64) + full compliance JSON.
    Also saves the result to the DB and emits via WebSocket (same as live check).
    """
    if not _DETECT_READY:
        return jsonify({"error": "Detection model not available on backend"}), 503

    # ── Validate image ────────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # ── Decode image bytes → OpenCV frame ─────────────────────────
    img_bytes = file.read()
    nparr     = np.frombuffer(img_bytes, np.uint8)
    frame     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return jsonify({"error": "Could not decode image — unsupported format"}), 400

    # ── Resolve employee from form data ───────────────────────────
    employee_id = request.form.get("employee_id", "").strip()
    employees   = _load_employees()
    employee    = next((e for e in employees if e["id"] == employee_id), None)

    # Fallback: use provided fields or defaults
    if not employee:
        employee = {
            "id":         employee_id or "UPLOAD",
            "name":       request.form.get("employee_name", "Demo Worker"),
            "department": request.form.get("department",    "Demo"),
            "role":       request.form.get("role",          "Worker"),
        }

    camera_id = request.form.get("camera_id", "IMG-UPLOAD")

    # ── Run PPE detection (same call as live camera) ───────────────
    detections = _detector.detect(frame)
    compliance = _detector.check_ppe_compliance(detections)

    # ── Safety evaluation (unchanged algorithm) ───────────────────
    status_data = _safety.evaluate(compliance)

    # Compute safety percentage (same formula as per_person_compliance)
    found = sum([
        status_data["has_helmet"],
        status_data["has_vest"],
        status_data["has_gloves"],
        status_data["has_goggles"],
        status_data["has_boots"],
    ])
    safety_pct = int(round((found / 5) * 100))
    status_data["safety_percentage"] = safety_pct
    status_data["track_id"]          = None

    # ── Draw bounding boxes on the annotated frame ────────────────
    annotated = _detector.draw_boxes(frame.copy(), detections)

    # Encode annotated image to base64 PNG
    success, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 88])
    if not success:
        return jsonify({"error": "Failed to encode annotated image"}), 500

    annotated_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

    # ── Save to DB (full log) ─────────────────────────────────────
    missing_str = ", ".join(compliance.get("missing", []))
    log = EmployeeCheckLog(
        employee_id   = employee["id"],
        employee_name = employee["name"],
        department    = employee.get("department", ""),
        role          = employee.get("role",       ""),
        has_helmet    = status_data["has_helmet"],
        has_vest      = status_data["has_vest"],
        has_gloves    = status_data["has_gloves"],
        has_goggles   = status_data["has_goggles"],
        has_boots     = status_data["has_boots"],
        missing_ppe   = missing_str,
        status        = status_data["status"],
        camera_id     = camera_id
    )
    db.session.add(log)

    # Update or create latest status row
    existing = EmployeeLatestStatus.query.filter_by(
        employee_id=employee["id"]
    ).first()
    if existing:
        existing.employee_name = employee["name"]
        existing.department    = employee.get("department", "")
        existing.role          = employee.get("role",       "")
        existing.has_helmet    = status_data["has_helmet"]
        existing.has_vest      = status_data["has_vest"]
        existing.has_gloves    = status_data["has_gloves"]
        existing.has_goggles   = status_data["has_goggles"]
        existing.has_boots     = status_data["has_boots"]
        existing.missing_ppe   = missing_str
        existing.status        = status_data["status"]
        existing.last_checked  = datetime.utcnow()
        existing.camera_id     = camera_id
    else:
        latest = EmployeeLatestStatus(
            employee_id   = employee["id"],
            employee_name = employee["name"],
            department    = employee.get("department", ""),
            role          = employee.get("role",       ""),
            has_helmet    = status_data["has_helmet"],
            has_vest      = status_data["has_vest"],
            has_gloves    = status_data["has_gloves"],
            has_goggles   = status_data["has_goggles"],
            has_boots     = status_data["has_boots"],
            missing_ppe   = missing_str,
            status        = status_data["status"],
            camera_id     = camera_id
        )
        db.session.add(latest)

    db.session.commit()

    # ── Emit real-time WebSocket update → dashboard ───────────────
    realtime_payload = {
        "employee_id":       employee["id"],
        "employee_name":     employee["name"],
        "department":        employee.get("department", ""),
        "has_helmet":        status_data["has_helmet"],
        "has_vest":          status_data["has_vest"],
        "has_gloves":        status_data["has_gloves"],
        "has_goggles":       status_data["has_goggles"],
        "has_boots":         status_data["has_boots"],
        "missing_ppe":       compliance.get("missing", []),
        "status":            status_data["status"],
        "safety_percentage": safety_pct,
        "track_id":          None,
        "camera_id":         camera_id,
        "timestamp":         datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    if socketio:
        socketio.emit("check_update", realtime_payload)
        print(f"[WebSocket] Image upload result → {employee['id']} | {status_data['status']}")

    print(f"[Detect-Image] {employee['id']} : {employee['name']} | {status_data['status']} | {safety_pct}%")

    # ── Return JSON response ───────────────────────────────────────
    return jsonify({
        "status":            "ok",
        "log_id":            log.id,
        "employee_id":       employee["id"],
        "employee_name":     employee["name"],
        "department":        employee.get("department", ""),
        "role":              employee.get("role",       ""),
        "has_helmet":        status_data["has_helmet"],
        "has_vest":          status_data["has_vest"],
        "has_gloves":        status_data["has_gloves"],
        "has_goggles":       status_data["has_goggles"],
        "has_boots":         status_data["has_boots"],
        "missing_ppe":       compliance.get("missing", []),
        "result":            status_data["status"],
        "message":           status_data["message"],
        "safety_percentage": safety_pct,
        "detection_count":   len(detections),
        "annotated_image":   annotated_b64,
        "camera_id":         camera_id,
        "timestamp":         datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }), 200