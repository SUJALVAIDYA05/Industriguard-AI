from flask import Blueprint, jsonify, request
from database import db
from models import ViolationLog, AlertLog
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/logs", methods=["GET"])
def get_logs():
    """Returns recent violation logs for the logs table"""
    limit = request.args.get("limit", 50, type=int)

    logs = ViolationLog.query\
        .order_by(ViolationLog.timestamp.desc())\
        .limit(limit)\
        .all()

    return jsonify([l.to_dict() for l in logs])


@dashboard_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Returns summary statistics for the dashboard cards.
    - Total violations today
    - HIGH risk count today
    - Most common missing PPE
    - Risk level distribution
    """
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    # Total logs today
    total_today = ViolationLog.query\
        .filter(ViolationLog.timestamp >= today_start)\
        .count()

    # HIGH risk today
    high_today = ViolationLog.query\
        .filter(
            ViolationLog.timestamp >= today_start,
            ViolationLog.risk_level == "HIGH"
        ).count()

    # Risk level distribution (all time)
    distribution = db.session.query(
        ViolationLog.risk_level,
        func.count(ViolationLog.id).label("count")
    ).group_by(ViolationLog.risk_level).all()

    dist_dict = {row.risk_level: row.count for row in distribution}

    # Average score today
    avg_score_result = db.session.query(
        func.avg(ViolationLog.score)
    ).filter(ViolationLog.timestamp >= today_start).scalar()

    avg_score = round(avg_score_result or 0, 1)

    # Unresolved alerts count
    unresolved = AlertLog.query\
        .filter(AlertLog.resolved == False)\
        .count()

    return jsonify({
        "total_today":    total_today,
        "high_today":     high_today,
        "avg_score":      avg_score,
        "unresolved_alerts": unresolved,
        "distribution": {
            "LOW":    dist_dict.get("LOW", 0),
            "MEDIUM": dist_dict.get("MEDIUM", 0),
            "HIGH":   dist_dict.get("HIGH", 0)
        }
    })


@dashboard_bp.route("/api/trend", methods=["GET"])
def get_trend():
    """
    Returns hourly risk counts for the last 24 hours.
    Used to draw the trend chart on dashboard.
    """
    since = datetime.utcnow() - timedelta(hours=24)

    logs = ViolationLog.query\
        .filter(ViolationLog.timestamp >= since)\
        .all()

    # Group by hour
    hourly = {}
    for log in logs:
        hour = log.timestamp.strftime("%H:00")
        if hour not in hourly:
            hourly[hour] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        hourly[hour][log.risk_level] += 1

    # Sort by hour
    sorted_trend = [
        {"hour": hour, **counts}
        for hour, counts in sorted(hourly.items())
    ]

    return jsonify(sorted_trend)


@dashboard_bp.route("/api/health", methods=["GET"])
def health_check():
    """Simple health check — lets frontend know backend is alive"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "service": "IndustriGuard AI Backend"
    })