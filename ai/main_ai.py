import cv2
import time
import os
import sys

from config import (
    CAMERA_SOURCE,
    BACKEND_URL,
    MODEL_PATH,
    EMPLOYEES_FILE,
    REPORT_PATH,
    RESULT_DISPLAY_SECONDS,
    PPE_FRAMES_NEEDED,
    CAMERA_ID
)

from camera_feed    import CameraFeed
from qr_scanner     import QRScanner
from ppe_detector   import PPEDetector
from safety_status  import SafetyStatus
from excel_reporter import ExcelReporter
from reporter       import Reporter

# ── Configuration ──────────────────────────────────────────────────
# For mobile camera, replace with your phone's IP:
# CAMERA_SOURCE = "http://192.168.x.x:8080/video"
CAMERA_SOURCE   = 0
MODEL_PATH      = "yolov8n.pt"
EMPLOYEES_FILE  = "../employee_data/employees.json"
REPORT_PATH     = "../reports/employee_safety.xlsx"


# How many seconds to show result before resetting for next worker
RESULT_DISPLAY_SECONDS = 5

# ── Startup ────────────────────────────────────────────────────────
print("\n" + "="*55)
print("   IndustriGuard AI — QR + PPE Safety Check System")
print("="*55 + "\n")

camera   = CameraFeed()                              # reads from config
scanner  = QRScanner(employees_file=EMPLOYEES_FILE)
detector = PPEDetector(model_path=MODEL_PATH)
safety   = SafetyStatus()
reporter = ExcelReporter(report_path=REPORT_PATH)
reporter_backend = Reporter(backend_url=BACKEND_URL)

cam_info = camera.get_info()
print(f"\n[Camera] Type   : {cam_info['type']}")
print(f"[Camera] Source : {cam_info['source']}")
print(f"[Camera] Size   : {cam_info['width']}x{cam_info['height']}")
print(f"[Camera] FPS    : {cam_info['fps']}")

print("\n[System] All modules ready.\n")
print("HOW TO USE:")
print("  1. Worker holds QR ID card toward camera")
print("  2. System scans QR → identifies employee")
print("  3. System checks PPE (helmet, vest)")
print("  4. Shows READY / NOT READY on screen")
print("  5. Result saved to Excel report")
print("\nPress Q to quit.\n")
print("-" * 55)

# ── State Machine ──────────────────────────────────────────────────
#
#  SCANNING   → waiting for QR code
#  CHECKING   → QR found, running PPE check
#  DISPLAYING → showing result, countdown to reset
#  RESET      → clear state, back to SCANNING
#
STATE             = "SCANNING"
current_employee  = None
current_status    = None
result_timer      = None
ppe_check_frames  = 0
PPE_FRAMES_NEEDED = 10   # Analyze 10 frames to confirm PPE status
ppe_results_pool  = []   # Collect results over multiple frames

while True:
    frame = camera.get_frame()
    if frame is None:
        print("[Main] No frame received. Exiting.")
        break

    h, w = frame.shape[:2]

    # ── Top instruction banner ─────────────────────────────────────
    cv2.rectangle(frame, (0, 0), (w, 50), (20, 60, 120), -1)
    cv2.putText(
        frame,
        "IndustriGuard AI — Safety Check Station",
        (15, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75, (255, 255, 255), 2
    )

    # ══════════════════════════════════════════════════════════════
    # STATE: SCANNING — Wait for QR code
    # ══════════════════════════════════════════════════════════════
    if STATE == "SCANNING":

        # Show instruction
        cv2.putText(
            frame,
            "Please show your QR ID Card to the camera",
            (w // 2 - 250, h // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 0), 2
        )

        # Scanning border animation (yellow box in center)
        box_x1, box_y1 = w // 2 - 150, h // 2 - 150
        box_x2, box_y2 = w // 2 + 150, h // 2 + 100
        cv2.rectangle(frame, (box_x1, box_y1), (box_x2, box_y2),
                      (0, 255, 255), 2)
        cv2.putText(
            frame, "[ SCAN AREA ]",
            (box_x1 + 30, box_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 255, 255), 1
        )

        # Try to scan QR
        employee = scanner.scan_frame(frame)
        frame    = scanner.draw_qr_overlay(frame, employee)

        if employee:
            current_employee = employee
            ppe_check_frames = 0
            ppe_results_pool = []
            STATE = "CHECKING"
            print(f"\n[Main] QR Scanned → {employee['id']} : {employee['name']}")
            print("[Main] Starting PPE check...")

    # ══════════════════════════════════════════════════════════════
    # STATE: CHECKING — QR found, now check PPE
    # ══════════════════════════════════════════════════════════════
    elif STATE == "CHECKING":

        # Show checking banner
        cv2.rectangle(frame, (0, 55), (w, 95), (20, 100, 20), -1)
        cv2.putText(
            frame,
            f"Checking PPE for: {current_employee['name']}  "
            f"({ppe_check_frames}/{PPE_FRAMES_NEEDED})",
            (15, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (255, 255, 255), 2
        )

        # Run PPE detection on this frame
        detections = detector.detect(frame)
        compliance = detector.check_ppe_compliance(detections)
        frame      = detector.draw_boxes(frame, detections)

        # Collect result
        ppe_results_pool.append(compliance)
        ppe_check_frames += 1

        # After enough frames, make final decision
        if ppe_check_frames >= PPE_FRAMES_NEEDED:

            # Majority vote across collected frames
            helmet_votes = sum(1 for r in ppe_results_pool if r["has_helmet"])
            vest_votes   = sum(1 for r in ppe_results_pool if r["has_vest"])

            final_compliance = {
                "has_helmet": helmet_votes >= PPE_FRAMES_NEEDED // 2,
                "has_vest":   vest_votes   >= PPE_FRAMES_NEEDED // 2,
                "missing":    []
            }
            if not final_compliance["has_helmet"]:
                final_compliance["missing"].append("Helmet")
            if not final_compliance["has_vest"]:
                final_compliance["missing"].append("Safety Vest")

            # Evaluate final status
            current_status = safety.evaluate(final_compliance)

            # Save to Excel
            reporter.update_employee(current_employee, current_status)
            # Send to backend
            reporter_backend.send_check_result(current_employee, current_status)

            result_timer = time.time()
            STATE = "DISPLAYING"
            print(f"[Main] Result → {current_status['status']}")

    # ══════════════════════════════════════════════════════════════
    # STATE: DISPLAYING — Show result, then reset
    # ══════════════════════════════════════════════════════════════
    elif STATE == "DISPLAYING":

        # Draw status overlay
        frame = safety.draw_status(frame, current_status, current_employee)

        # Countdown timer
        elapsed   = time.time() - result_timer
        remaining = int(RESULT_DISPLAY_SECONDS - elapsed)

        cv2.putText(
            frame,
            f"Next check in {remaining}s...",
            (w - 220, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (200, 200, 200), 1
        )

        # Excel saved confirmation
        cv2.putText(
            frame,
            "✓ Saved to Excel Report",
            (w - 250, h - 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 255, 100), 2
        )

        # Auto reset after display time
        if elapsed >= RESULT_DISPLAY_SECONDS:
            STATE = "SCANNING"
            scanner.reset()
            current_employee = None
            current_status   = None
            print("\n[Main] Ready for next worker...\n" + "-"*55)

    # ── Show frame ─────────────────────────────────────────────────
    cv2.imshow("IndustriGuard AI — Safety Check", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n[Main] Shutting down...")
        break

camera.release()
print("[Main] System stopped.\n")