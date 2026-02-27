from datetime import datetime
from database import db

class ViolationLog(db.Model):
    """
    Stores every safety event reported by the AI layer.
    One record = one detection cycle from the camera.
    """
    __tablename__ = "violation_logs"

    id                 = db.Column(db.Integer, primary_key=True)
    timestamp          = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level         = db.Column(db.String(10), nullable=False)  # LOW / MEDIUM / HIGH
    score              = db.Column(db.Float, nullable=False)
    missing_ppe        = db.Column(db.String(200), default="")     # "Helmet, Safety Vest"
    posture_deviation  = db.Column(db.Float, default=0.0)
    inactivity_seconds = db.Column(db.Float, default=0.0)
    ppe_score          = db.Column(db.Float, default=0.0)
    posture_score      = db.Column(db.Float, default=0.0)
    inactivity_score   = db.Column(db.Float, default=0.0)
    camera_id          = db.Column(db.String(50), default="CAM-01")

    def to_dict(self):
        """Converts record to dictionary for JSON responses"""
        return {
            "id":                 self.id,
            "timestamp":          self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "risk_level":         self.risk_level,
            "score":              self.score,
            "missing_ppe":        self.missing_ppe,
            "posture_deviation":  self.posture_deviation,
            "inactivity_seconds": self.inactivity_seconds,
            "ppe_score":          self.ppe_score,
            "posture_score":      self.posture_score,
            "inactivity_score":   self.inactivity_score,
            "camera_id":          self.camera_id
        }


class AlertLog(db.Model):
    """
    Stores only HIGH and MEDIUM alerts separately.
    Useful for the alert panel on the dashboard.
    """
    __tablename__ = "alert_logs"

    id          = db.Column(db.Integer, primary_key=True)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level  = db.Column(db.String(10), nullable=False)
    score       = db.Column(db.Float, nullable=False)
    missing_ppe = db.Column(db.String(200), default="")
    camera_id   = db.Column(db.String(50), default="CAM-01")
    resolved    = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id":          self.id,
            "timestamp":   self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "risk_level":  self.risk_level,
            "score":       self.score,
            "missing_ppe": self.missing_ppe,
            "camera_id":   self.camera_id,
            "resolved":    self.resolved
        }