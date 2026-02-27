from datetime import datetime
from database import db


class EmployeeCheckLog(db.Model):
    """
    One record per employee safety check.
    Stores who was checked, when, and what the result was.
    """
    __tablename__ = "employee_check_logs"

    id                 = db.Column(db.Integer, primary_key=True)
    timestamp          = db.Column(db.DateTime, default=datetime.utcnow)

    # Employee info
    employee_id        = db.Column(db.String(20), nullable=False)
    employee_name      = db.Column(db.String(100), nullable=False)
    department         = db.Column(db.String(100), default="")
    role               = db.Column(db.String(100), default="")

    # PPE results
    has_helmet         = db.Column(db.Boolean, default=False)
    has_vest           = db.Column(db.Boolean, default=False)
    missing_ppe        = db.Column(db.String(200), default="")

    # Final decision
    status             = db.Column(db.String(15), nullable=False)  # READY / NOT READY

    # Camera info
    camera_id          = db.Column(db.String(50), default="CAM-01")

    def to_dict(self):
        return {
            "id":            self.id,
            "timestamp":     self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "employee_id":   self.employee_id,
            "employee_name": self.employee_name,
            "department":    self.department,
            "role":          self.role,
            "has_helmet":    self.has_helmet,
            "has_vest":      self.has_vest,
            "missing_ppe":   self.missing_ppe,
            "status":        self.status,
            "camera_id":     self.camera_id
        }


class EmployeeLatestStatus(db.Model):
    """
    Stores only the LATEST check result per employee.
    This is what the dashboard summary table shows.
    One row per employee — updated every time they are checked.
    """
    __tablename__ = "employee_latest_status"

    id                 = db.Column(db.Integer, primary_key=True)
    employee_id        = db.Column(db.String(20), unique=True, nullable=False)
    employee_name      = db.Column(db.String(100), nullable=False)
    department         = db.Column(db.String(100), default="")
    role               = db.Column(db.String(100), default="")
    has_helmet         = db.Column(db.Boolean, default=False)
    has_vest           = db.Column(db.Boolean, default=False)
    missing_ppe        = db.Column(db.String(200), default="")
    status             = db.Column(db.String(15), nullable=False)
    last_checked       = db.Column(db.DateTime, default=datetime.utcnow)
    camera_id          = db.Column(db.String(50), default="CAM-01")

    def to_dict(self):
        return {
            "id":            self.id,
            "employee_id":   self.employee_id,
            "employee_name": self.employee_name,
            "department":    self.department,
            "role":          self.role,
            "has_helmet":    self.has_helmet,
            "has_vest":      self.has_vest,
            "missing_ppe":   self.missing_ppe,
            "status":        self.status,
            "last_checked":  self.last_checked.strftime("%Y-%m-%d %H:%M:%S"),
            "camera_id":     self.camera_id
        }