# ═══════════════════════════════════════════════════════════
#   IndustriGuard AI — Central Configuration
#   Edit this file when your camera or network changes
# ═══════════════════════════════════════════════════════════

# ── Camera Mode ───────────────────────────────────────────
# Options:
#   "usb_mobile"   → Mobile phone connected via USB (DroidCam, Iriun, Camo, etc.)
#   "usb_tether"   → Mobile phone via USB Tethering + IP Webcam app
#   "wifi"         → Mobile camera over WiFi (IP Webcam app)
#   "webcam"       → Laptop built-in webcam
#   "video"        → Recorded video file (for testing)

# Default to laptop webcam so the app works out-of-the-box.
# Switch to "usb_mobile" / "usb_tether" / "wifi" when using a phone camera.
CAMERA_MODE = "usb_mobile"

# ── USB Mobile Settings (DroidCam / Iriun / Camo) ────────
# When you connect your phone via USB with DroidCam or Iriun,
# it creates a virtual webcam. Set the device index below.
# Usually:  0 = laptop webcam,  1 = USB phone camera
# Run  python find_cameras.py  to auto-detect the correct index.

USB_CAMERA_INDEX = 1

# ── USB Tethering Settings (IP Webcam app) ────────────────
# If using IP Webcam app with USB tethering enabled:
# The phone usually gets IP 192.168.42.129 over USB tether.
# Open IP Webcam app on phone → "Start Server" → note the port.

USB_TETHER_IP   = "192.168.42.129"
USB_TETHER_PORT = 8080

# ── WiFi Mobile Camera (IP Webcam app over WiFi) ─────────
WIFI_CAMERA_URL = "http://192.168.0.101:8080/video"

# ── Video File (testing mode) ─────────────────────────────
VIDEO_FILE_PATH = "test_video.mp4"

# ── Backend Settings ──────────────────────────────────────
BACKEND_URL = "http://localhost:5000"

# ── AI Model Settings ────────────────────────────────────
MODEL_PATH = "ppe_model.pt"  # Trained PPE model (25 classes: PPE, vehicles, equipment, person)

# ── Tracking Settings ───────────────────────────────────────
# Enables Ultralytics ByteTrack for stable person IDs across frames.
USE_BYTE_TRACK = True

# ── Performance Settings ────────────────────────────────────
# Run the heavy YOLO+tracking step only every N frames.
# (Higher = faster, but overlays update less frequently.)
INFERENCE_EVERY_N_FRAMES = 3

# Reduce the input size for faster inference. (Typical: 480 or 640)
# Set to None to use original frame size.
INFERENCE_IMG_SIZE = 480

# Turn off extra detector box drawing (saves CPU/GPU and avoids clutter)
DRAW_DETECTOR_BOXES = False

# Keep worker info visible on screen for a few seconds after brief detection dropouts.
WORKER_INFO_PERSIST_SECONDS = 5

# ── Logging ────────────────────────────────────────────────
# Reduce terminal spam for better performance/readability.
VERBOSE_LOGS = False

# ── File Paths ─────────────────────────────────────────────
EMPLOYEES_FILE = "../employee_data/employees.json"
REPORT_PATH    = "../reports/employee_safety.xlsx"

# ── System Settings ──────────────────────────────────────
# Seconds to display result before resetting for next worker
RESULT_DISPLAY_SECONDS = 5

# How many frames to analyze for PPE confirmation
PPE_FRAMES_NEEDED = 10

# Camera ID shown in logs
CAMERA_ID = "CAM-01"