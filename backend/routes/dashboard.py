from flask import Blueprint, jsonify, request
from database import db
from models import EmployeeCheckLog, EmployeeLatestStatus
from datetime import datetime, timedelta
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


# ── Summary stats for dashboard cards ─────────────────────────────
@dashboard_bp.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Returns summary numbers for the dashboard top cards.
    - Total employees checked today
    - Ready count
    - Not Ready count
    - Ready percentage
    """
    today       = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    # ── Today's checks ─────────────────────────────────────────────
    total_today = EmployeeCheckLog.query\
        .filter(EmployeeCheckLog.timestamp >= today_start)\
        .count()

    ready_today = EmployeeCheckLog.query\
        .filter(
            EmployeeCheckLog.timestamp >= today_start,
            EmployeeCheckLog.status == "READY"
        ).count()

    not_ready_today = EmployeeCheckLog.query\
        .filter(
            EmployeeCheckLog.timestamp >= today_start,
            EmployeeCheckLog.status == "NOT READY"
        ).count()

    # ── Current status (latest per employee) ───────────────────────
    total_employees = EmployeeLatestStatus.query.count()

    currently_ready = EmployeeLatestStatus.query\
        .filter_by(status="READY").count()

    currently_not_ready = EmployeeLatestStatus.query\
        .filter_by(status="NOT READY").count()

    # ── Most common missing PPE ────────────────────────────────────
    no_helmet_count = EmployeeCheckLog.query\
        .filter(
            EmployeeCheckLog.timestamp >= today_start,
            EmployeeCheckLog.has_helmet == False
        ).count()

    no_vest_count = EmployeeCheckLog.query\
        .filter(
            EmployeeCheckLog.timestamp >= today_start,
            EmployeeCheckLog.has_vest == False
        ).count()

    # ── Ready percentage ───────────────────────────────────────────
    ready_pct = 0
    if total_today > 0:
        ready_pct = round((ready_today / total_today) * 100, 1)

    return jsonify({
        "today": {
            "total_checks":     total_today,
            "ready":            ready_today,
            "not_ready":        not_ready_today,
            "ready_percentage": ready_pct
        },
        "current": {
            "total_employees":  total_employees,
            "ready":            currently_ready,
            "not_ready":        currently_not_ready
        },
        "ppe_violations": {
            "no_helmet": no_helmet_count,
            "no_vest":   no_vest_count
        }
    })


# ── Trend data for chart ───────────────────────────────────────────
@dashboard_bp.route("/api/trend", methods=["GET"])
def get_trend():
    """
    Returns hourly READY vs NOT READY counts
    for the last 24 hours.
    Used to draw the trend chart.
    """
    since = datetime.utcnow() - timedelta(hours=24)

    logs = EmployeeCheckLog.query\
        .filter(EmployeeCheckLog.timestamp >= since)\
        .all()

    # Group by hour
    hourly = {}
    for log in logs:
        hour = log.timestamp.strftime("%H:00")
        if hour not in hourly:
            hourly[hour] = {"READY": 0, "NOT READY": 0}
        hourly[hour][log.status] += 1

    sorted_trend = [
        {
            "hour":      hour,
            "ready":     counts["READY"],
            "not_ready": counts["NOT READY"]
        }
        for hour, counts in sorted(hourly.items())
    ]

    return jsonify(sorted_trend)


# ── Department breakdown ───────────────────────────────────────────
@dashboard_bp.route("/api/departments", methods=["GET"])
def get_department_stats():
    """
    Returns compliance stats grouped by department.
    Useful for management to see which department
    has the most PPE violations.
    """
    today       = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    results = db.session.query(
        EmployeeCheckLog.department,
        EmployeeCheckLog.status,
        func.count(EmployeeCheckLog.id).label("count")
    ).filter(
        EmployeeCheckLog.timestamp >= today_start
    ).group_by(
        EmployeeCheckLog.department,
        EmployeeCheckLog.status
    ).all()

    # Build department dict
    dept_data = {}
    for row in results:
        dept = row.department or "Unknown"
        if dept not in dept_data:
            dept_data[dept] = {"READY": 0, "NOT READY": 0}
        dept_data[dept][row.status] += 1

    dept_list = [
        {
            "department": dept,
            "ready":      counts["READY"],
            "not_ready":  counts["NOT READY"]
        }
        for dept, counts in dept_data.items()
    ]

    return jsonify(dept_list)


# ── Health check ───────────────────────────────────────────────────
@dashboard_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status":    "running",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "service":   "IndustriGuard AI Backend v2"
    })