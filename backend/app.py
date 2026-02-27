from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from database import db, init_db
from routes.checks import checks_bp, init_checks
from routes.dashboard import dashboard_bp

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"]                     = "industriguard_secret_2025"
    app.config["SQLALCHEMY_DATABASE_URI"]        = "sqlite:///industriguard.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app, origins="*")

    # Initialize database with new models
    init_db(app)

    # Register blueprints
    app.register_blueprint(checks_bp)
    app.register_blueprint(dashboard_bp)

    return app


# ── Create app and SocketIO ────────────────────────────────────────
app      = create_app()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Inject socketio into checks route
init_checks(socketio)


# ── WebSocket events ───────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    print("[WebSocket] Dashboard client connected")
    socketio.emit("connected", {
        "message": "Connected to IndustriGuard backend",
        "service": "IndustriGuard AI v2"
    })

@socketio.on("disconnect")
def on_disconnect():
    print("[WebSocket] Dashboard client disconnected")


# ── Run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  IndustriGuard AI — Backend v2 Starting")
    print("="*55)
    print("[Backend] Running on http://localhost:5000\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )