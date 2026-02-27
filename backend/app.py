from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from database import db, init_db
from routes.alerts import alerts_bp, init_alerts
from routes.dashboard import dashboard_bp
import os

# ── App Configuration ──────────────────────────────────────────────
def create_app():
    app = Flask(__name__)

    # Config
    app.config["SECRET_KEY"]                   = "industriguard_secret_key_2025"
    app.config["SQLALCHEMY_DATABASE_URI"]      = "sqlite:///industriguard.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Extensions
    CORS(app, origins="*")

    # Initialize database
    init_db(app)

    # Register route blueprints
    app.register_blueprint(alerts_bp)
    app.register_blueprint(dashboard_bp)

    return app


# ── Create App and SocketIO ────────────────────────────────────────
app = create_app()
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# Inject socketio into alerts route
init_alerts(socketio)


# ── WebSocket Events ───────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print("[WebSocket] Dashboard client connected")
    socketio.emit("safety_update", {
        "risk_level": "LOW",
        "score": 0,
        "missing_ppe": [],
        "message": "Connected to IndustriGuard backend"
    })

@socketio.on("disconnect")
def on_disconnect():
    print("[WebSocket] Dashboard client disconnected")


# ── Run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  IndustriGuard AI — Backend Starting")
    print("="*50)
    print("\n[Backend] Running on http://localhost:5000\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )