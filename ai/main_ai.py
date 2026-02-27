import cv2
import time
from camera_feed import CameraFeed
from ppe_detector import PPEDetector
from pose_estimator import PoseEstimator
from risk_scorer import RiskScorer
from alert_engine import AlertEngine

# ── Configuration ──────────────────────────────────────────────────
CAMERA_SOURCE  = 0               # 0 = webcam, or "video.mp4" for testing
MODEL_PATH     = "yolov8n.pt"    # Replace with PPE model later
BACKEND_URL    = "http://localhost:5000"

# ── Initialize all modules ─────────────────────────────────────────
print("\n" + "="*50)
print("  IndustriGuard AI — Starting Up")
print("="*50 + "\n")

camera  = CameraFeed(source=CAMERA_SOURCE)
detector = PPEDetector(model_path=MODEL_PATH)
pose    = PoseEstimator()
scorer  = RiskScorer()
alerts  = AlertEngine(backend_url=BACKEND_URL)

print("\n[System] All modules loaded. Starting surveillance...\n")
print("Press Q to quit.\n")

# ── Risk level display config ──────────────────────────────────────
RISK_COLORS = {
    "LOW":    (0, 255, 0),     # Green
    "MEDIUM": (0, 165, 255),   # Orange
    "HIGH":   (0, 0, 255)      # Red
}

# ── Main loop ──────────────────────────────────────────────────────
frame_count = 0
fps_time = time.time()

while True:
    frame = camera.get_frame()
    if frame is None:
        print("[Main] No frame received. Exiting.")
        break

    frame_count += 1

    # ── 1. PPE Detection ───────────────────────────────────────────
    detections = detector.detect(frame)
    compliance = detector.check_ppe_compliance(detections)
    frame = detector.draw_boxes(frame, detections)

    # ── 2. Pose Estimation ─────────────────────────────────────────
    landmarks = pose.estimate(frame)
    frame = pose.draw_skeleton(frame, landmarks)
    posture_data = pose.get_posture_data(landmarks)
    posture_deviation = pose.get_posture_deviation(posture_data)

    inactivity = posture_data["inactivity_seconds"] if posture_data else 0

    # ── 3. Risk Scoring ────────────────────────────────────────────
    risk_level, score, breakdown = scorer.calculate(
        compliance, posture_deviation, inactivity
    )

    # ── 4. Alert Engine ────────────────────────────────────────────
    alerts.trigger(risk_level, score, breakdown, compliance, posture_data)

    # ── 5. Draw HUD on frame ───────────────────────────────────────
    color = RISK_COLORS[risk_level]
    h, w = frame.shape[:2]

    # Risk level banner at top
    cv2.rectangle(frame, (0, 0), (w, 60), color, -1)
    cv2.putText(
        frame,
        f"  RISK: {risk_level}   |   Score: {score}/100",
        (10, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0, (255, 255, 255), 2
    )

    # PPE status
    ppe_text = "PPE: "
    ppe_text += "✓ Helmet  " if compliance["has_helmet"] else "✗ No Helmet  "
    ppe_text += "✓ Vest" if compliance["has_vest"] else "✗ No Vest"

    cv2.putText(
        frame, ppe_text,
        (10, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65, color, 2
    )

    # Posture info
    if posture_data:
        cv2.putText(
            frame,
            f"Posture Deviation: {posture_deviation}  |  "
            f"Inactivity: {inactivity:.1f}s",
            (10, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (200, 200, 200), 1
        )

    # FPS counter
    fps = frame_count / (time.time() - fps_time)
    cv2.putText(
        frame, f"FPS: {fps:.1f}",
        (w - 120, h - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6, (150, 150, 150), 1
    )

    # ── 6. Display ─────────────────────────────────────────────────
    cv2.imshow("IndustriGuard AI — Surveillance", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n[Main] Q pressed. Shutting down...")
        break

camera.release()
print("[Main] IndustriGuard AI stopped.\n")