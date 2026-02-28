# ═══════════════════════════════════════════════════════════
#   IndustriGuard AI — Central Configuration
#   Edit this file when your network changes
# ═══════════════════════════════════════════════════════════

# ── Camera Settings ────────────────────────────────────────
# Options:
#   0                              → Laptop webcam (fallback)
#   "http://192.168.x.x:8080/video" → Mobile camera (primary)
#   "video.mp4"                    → Recorded video (testing)

CAMERA_SOURCE = "http://192.168.0.101:8080/video"

# Set to True to use webcam instead (quick fallback)
USE_WEBCAM_FALLBACK = False

# ── Backend Settings ───────────────────────────────────────
BACKEND_URL = "http://localhost:5000"

# ── AI Model Settings ──────────────────────────────────────
MODEL_PATH = "yolov8n.pt"  # Replace with PPE model later

# ── File Paths ─────────────────────────────────────────────
EMPLOYEES_FILE = "../employee_data/employees.json"
REPORT_PATH    = "../reports/employee_safety.xlsx"

# ── System Settings ────────────────────────────────────────
# Seconds to display result before resetting for next worker
RESULT_DISPLAY_SECONDS = 5

# How many frames to analyze for PPE confirmation
PPE_FRAMES_NEEDED = 10

# Camera ID shown in logs
CAMERA_ID = "CAM-01"