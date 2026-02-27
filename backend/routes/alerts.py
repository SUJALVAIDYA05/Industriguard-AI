from flask import Blueprint, request, jsonify
from flask_socketio import emit
from database import db
from models import ViolationLog, AlertLog
from datetime import datetime

alerts_bp = Blueprint("alerts", __name__)

# We'll inject socketio from app.py
socketio = None

def init_alerts(sio):
    """Called from app.py to inject socketio instance"""
    global socketio
    socketio = sio


@alerts_bp.route("/api/report", methods=["POST"])
def receive_report():
    """
    AI layer sends data here every detection cycle.
    Stores in database and emits to dashboard via WebSocket.
    """
    data = request.json

    if not data:
        return jsonify({"error": "No data received"}), 400

    risk_level  = data.get("risk_level", "LOW")
    score       = data.get("score", 0)
    breakdown   = data.get("breakdown", {})
    missing_ppe = ", ".join(data.get("missing_ppe", []))
    camera_id   = data.get("camera_id", "CAM-01")

    # ── Save to ViolationLog (every report) ───────────────────────
    log = ViolationLog(
        risk_level         = risk_level,
        score              = score,
        missing_ppe        = missing_ppe,
        posture_deviation  = data.get("posture_deviation", 0),
        inactivity_seconds = data.get("inactivity_seconds", 0),
        ppe_score          = breakdown.get("ppe_score", 0),
        posture_score      = breakdown.get("posture_score", 0),
        inactivity_score   = breakdown.get("inactivity_score", 0),
        camera_id          = camera_id
    )
    db.session.add(log)

    # ── Save to AlertLog (only HIGH and MEDIUM) ───────────────────
    if risk_level in ["HIGH", "MEDIUM"]:
        alert = AlertLog(
            risk_level  = risk_level,
            score       = score,
            missing_ppe = missing_ppe,
            camera_id   = camera_id
        )
        db.session.add(alert)

    db.session.commit()

    # ── Emit real-time update to dashboard ────────────────────────
    payload = {
        "risk_level":         risk_level,
        "score":              score,
        "missing_ppe":        data.get("missing_ppe", []),
        "posture_deviation":  data.get("posture_deviation", 0),
        "inactivity_seconds": data.get("inactivity_seconds", 0),
        "camera_id":          camera_id,
        "timestamp":          datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }

    if socketio:
        socketio.emit("safety_update", payload)

    return jsonify({"status": "received", "id": log.id}), 200


@alerts_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Returns recent HIGH and MEDIUM alerts for the dashboard alert panel"""
    limit = request.args.get("limit", 20, type=int)

    alerts = AlertLog.query\
        .order_by(AlertLog.timestamp.desc())\
        .limit(limit)\
        .all()

    return jsonify([a.to_dict() for a in alerts])


@alerts_bp.route("/api/alerts/<int:alert_id>/resolve", methods=["PATCH"])
def resolve_alert(alert_id):
    """Marks an alert as resolved from the dashboard"""
    alert = AlertLog.query.get(alert_id)

    if not alert:
        return jsonify({"error": "Alert not found"}), 404

    alert.resolved = True
    db.session.commit()

    return jsonify({"status": "resolved", "id": alert_id})