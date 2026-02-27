from flask import Blueprint, request, jsonify
from database import db
from models import EmployeeCheckLog, EmployeeLatestStatus
from datetime import datetime

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
        "missing_ppe":   data.get("missing_ppe", []),
        "status":        status,
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