import cv2
import time
import os
import sys
import numpy as np

from config import (
    BACKEND_URL,
    MODEL_PATH,
    EMPLOYEES_FILE,
    REPORT_PATH,
    RESULT_DISPLAY_SECONDS,
    PPE_FRAMES_NEEDED,
    CAMERA_ID,
    USE_BYTE_TRACK,
    INFERENCE_EVERY_N_FRAMES,
    INFERENCE_IMG_SIZE,
    DRAW_DETECTOR_BOXES,
    WORKER_INFO_PERSIST_SECONDS
)

from camera_feed    import CameraFeed
from qr_scanner_opencv import QRScanner  # Using OpenCV QR detector (no pyzbar)
from ppe_detector   import PPEDetector
from safety_status  import SafetyStatus
from excel_reporter import ExcelReporter
from reporter       import Reporter
import ui_overlay as ui

# ── Startup ────────────────────────────────────────────────────────
print("\n" + "="*55)
print("   IndustriGuard AI — QR + PPE Safety Check System")
print("="*55 + "\n")

camera   = CameraFeed()                              # reads from config
scanner  = QRScanner(employees_file=EMPLOYEES_FILE)

# Check model file exists before initializing YOLO (prevents network download attempt)
if not os.path.exists(MODEL_PATH):
    print(f"[ERROR] Model file not found: {MODEL_PATH}")
    print("[ERROR] The YOLO model must be downloaded first.")
    print(f"[ERROR] Run:  python download_models.py {MODEL_PATH}")
    print("[ERROR]   (requires internet connectivity)")
    camera.release()
    sys.exit(1)

detector = PPEDetector(model_path=MODEL_PATH)
safety   = SafetyStatus()
reporter = ExcelReporter(report_path=REPORT_PATH)
reporter_backend = Reporter(backend_url=BACKEND_URL)

# Tracking state for stable labels (used when USE_BYTE_TRACK=True)
# Employee labels persist briefly even if tracking/QR drops for a few frames.
track_employee = {}     # track_id -> emp_dict (sticky while track is alive)
track_last_seen = {}    # track_id -> time.time()
recent_workers = {}     # emp_id -> latest overlay/report info

# Backend/Excel reporting de-dupe (multi-person mode)
MULTI_REPORT_MIN_INTERVAL_SECONDS = 5.0
last_sent = {}  # employee_id -> {"status": str, "has_helmet": bool, "has_vest": bool, "t": float}

# Cache last expensive inference results (for smooth FPS)
frame_index = 0
cached_detections = []
cached_persons_compliance = []

def _bbox_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0, (ax2 - ax1)) * max(0, (ay2 - ay1))
    area_b = max(0, (bx2 - bx1)) * max(0, (by2 - by1))
    denom = area_a + area_b - inter
    return float(inter / denom) if denom > 0 else 0.0

def _bbox_center(b):
    x1, y1, x2, y2 = b
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

def _dist2(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy

def _qr_poly_to_rect(qr_poly):
    pts = qr_poly.reshape(-1, 2)
    xs = pts[:, 0]
    ys = pts[:, 1]
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

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
ppe_results_pool  = []   # Collect results over multiple frames

# Countdown timer state
countdown_timer   = None
COUNTDOWN_SECONDS = 5

while True:
    frame = camera.get_frame()
    if frame is None:
        print("[Main] No frame received. Exiting.")
        break

    h, w = frame.shape[:2]

    # ── Multi-person overlay (QR → person bbox + PPE + safety%) ─────
    # Only run the expensive multi-person pipeline during SCANNING state.
    # During COUNTDOWN / CHECKING / DISPLAYING the single-person state
    # machine handles everything — no need for the heavy overlay loop.
    run_multi_overlay = (STATE == "SCANNING")
    try:
        if run_multi_overlay:
            qr_results = scanner.scan_frame_multi(frame)
        else:
            qr_results = []
        frame_index += 1

        should_infer = run_multi_overlay and (frame_index % max(1, int(INFERENCE_EVERY_N_FRAMES)) == 0)
        if should_infer:
            detections = (
                detector.detect_with_tracks_fast(frame, imgsz=INFERENCE_IMG_SIZE)
                if USE_BYTE_TRACK
                else detector.detect(frame)
            )
            cached_detections = detections
            cached_persons_compliance = detector.per_person_compliance(detections)
        else:
            detections = cached_detections

        if DRAW_DETECTOR_BOXES and detections:
            frame = detector.draw_boxes(frame, detections)

        persons_compliance = cached_persons_compliance
        now = time.time()

        # Mark currently visible tracks and keep them alive for a short grace period
        # so worker info does not disappear immediately on brief dropouts.
        visible_track_ids = set()
        for pc in (persons_compliance or []):
            tid = pc["person_det"].get("track_id")
            if tid is not None:
                tid = int(tid)
                visible_track_ids.add(tid)
                track_last_seen[tid] = now

        for tid in list(track_last_seen.keys()):
            if tid not in visible_track_ids and (now - track_last_seen[tid]) > WORKER_INFO_PERSIST_SECONDS:
                track_last_seen.pop(tid, None)
                track_employee.pop(tid, None)

        # Associate QR -> tracked person using IoU-first, distance fallback
        persons = [pc for pc in (persons_compliance or []) if pc.get("person_det")]

        # IoU pass
        used_person_idxs = set()
        for r in qr_results:
            emp = r.get("employee")
            poly = r.get("bbox")
            if not emp or poly is None:
                continue

            qr_rect = _qr_poly_to_rect(poly)

            best_i = None
            best_iou = 0.0
            for i, pc in enumerate(persons):
                if i in used_person_idxs:
                    continue
                pb = pc["person_det"]["bbox"]
                iou = _bbox_iou(qr_rect, pb)
                if iou > best_iou:
                    best_iou = iou
                    best_i = i

            if best_i is not None and best_iou >= 0.05:
                tid = persons[best_i]["person_det"].get("track_id")
                if tid is not None:
                    track_employee[int(tid)] = emp
                    used_person_idxs.add(best_i)

        # Distance fallback for any QR not assigned via IoU
        for r in qr_results:
            emp = r.get("employee")
            poly = r.get("bbox")
            if not emp or poly is None:
                continue

            qr_rect = _qr_poly_to_rect(poly)
            qc = _bbox_center(qr_rect)

            best_i = None
            best_d = None
            for i, pc in enumerate(persons):
                if i in used_person_idxs:
                    continue
                tid = pc["person_det"].get("track_id")
                if tid is None:
                    continue
                d = _dist2(qc, _bbox_center(pc["person_det"]["bbox"]))
                if best_d is None or d < best_d:
                    best_d = d
                    best_i = i

            if best_i is not None:
                tid = persons[best_i]["person_det"].get("track_id")
                if tid is not None:
                    track_employee[int(tid)] = emp
                    used_person_idxs.add(best_i)

        # Draw per-person overlays using stable track_id
        for pc in persons:
            pb = pc["person_det"]["bbox"]
            x1, y1, x2, y2 = pb
            tid = pc["person_det"].get("track_id")

            comp = pc
            has_helmet  = bool(comp.get("has_helmet"))
            has_vest    = bool(comp.get("has_vest"))
            has_gloves  = bool(comp.get("has_gloves"))
            has_goggles = bool(comp.get("has_goggles"))
            has_boots   = bool(comp.get("has_boots"))
            safety_pct = int(comp.get("safety_percentage") or 0)
            all_ppe = has_helmet and has_vest and has_gloves and has_goggles and has_boots
            status = "READY" if all_ppe else "NOT READY"

            emp = None
            if tid is not None and int(tid) in track_employee:
                emp = track_employee[int(tid)]

            if emp:
                color = ui.ACCENT_GREEN if status == "READY" else ui.ACCENT_RED
            else:
                color = ui.TEXT_MUTED

            ui.draw_person_bbox(frame, (x1, y1, x2, y2), color, is_identified=bool(emp))

            if emp:
                lines = [
                    f"{emp['name']} ({emp['id']})",
                    f"{emp.get('department','')} | {emp.get('role','')}",
                    f"Helmet: {'Y' if has_helmet else 'N'}  Vest: {'Y' if has_vest else 'N'}  Gloves: {'Y' if has_gloves else 'N'}",
                    f"Goggles: {'Y' if has_goggles else 'N'}  Boots: {'Y' if has_boots else 'N'}",
                    f"Safety: {safety_pct}%  Status: {status}",
                ]

                recent_workers[emp["id"]] = {
                    "name": emp["name"],
                    "id": emp["id"],
                    "department": emp.get("department", ""),
                    "role": emp.get("role", ""),
                    "has_helmet": has_helmet,
                    "has_vest": has_vest,
                    "safety_pct": safety_pct,
                    "status": status,
                    "last_seen": now,
                }

                # Permanent association + continuous reporting:
                # send to backend + update Excel when status changes or at a slow interval.
                emp_id = emp["id"]
                prev = last_sent.get(emp_id)
                should_send = False
                if prev is None:
                    should_send = True
                else:
                    changed = (
                        prev["status"] != status or
                        prev["has_helmet"] != has_helmet or
                        prev["has_vest"] != has_vest
                    )
                    if changed or (now - prev["t"]) >= MULTI_REPORT_MIN_INTERVAL_SECONDS:
                        should_send = True

                if should_send:
                    compliance = {
                        "has_helmet": has_helmet,
                        "has_vest": has_vest,
                        "has_gloves": has_gloves,
                        "has_goggles": has_goggles,
                        "has_boots": has_boots,
                        "missing": ([] if has_helmet else ["Helmet"]) +
                                   ([] if has_vest else ["Safety Vest"]) +
                                   ([] if has_gloves else ["Gloves"]) +
                                   ([] if has_goggles else ["Goggles"]) +
                                   ([] if has_boots else ["Boots"])
                    }
                    status_data = safety.evaluate(compliance)
                    status_data["safety_percentage"] = safety_pct
                    status_data["track_id"] = int(tid) if tid is not None else None

                    # Save/update local Excel (one row per employee)
                    reporter.update_employee(emp, status_data)
                    # Publish to backend -> WebSocket -> frontend
                    reporter_backend.send_check_result(emp, status_data, camera_id=CAMERA_ID)

                    last_sent[emp_id] = {
                        "status": status,
                        "has_helmet": has_helmet,
                        "has_vest": has_vest,
                        "t": now
                    }

                # Draw worker info card only for identified employees
                ui.draw_worker_info_card(frame, lines, (x1, y1, x2, y2), color, w, h)

        # Also draw QR overlays (helpful for debugging association)
        frame = scanner.draw_qr_overlay_multi(frame, qr_results)
    except Exception as e:
        # Keep the main loop resilient
        print(f"[Main] Multi-overlay error: {e}")

    # ── Top instruction banner ─────────────────────────────────────
    bar_h = ui.draw_top_banner(frame)

    # ══════════════════════════════════════════════════════════════
    # STATE: SCANNING — Wait for QR code
    # ══════════════════════════════════════════════════════════════
    if STATE == "SCANNING":
        ui.draw_scanning_state(frame, bar_h)

        # Reuse the first recognized employee from scan_frame_multi
        # instead of calling scan_frame again (avoids redundant QR decode).
        employee = None
        for r in qr_results:
            if r.get("employee"):
                employee = r["employee"]
                break

        # Draw overlay using cached multi-scan results
        frame = scanner.draw_qr_overlay_multi(frame, qr_results)

    if employee and STATE == "SCANNING":
        current_employee = employee
        ppe_check_frames = 0
        ppe_results_pool = []
        countdown_timer  = time.time()
        STATE = "COUNTDOWN"
        scanner.reset()   # stops scanner from re-triggering

 # ══════════════════════════════════════════════════════════════
    # STATE: COUNTDOWN — Professional 5 second prep timer
    # ══════════════════════════════════════════════════════════════
    elif STATE == "COUNTDOWN":

        elapsed   = time.time() - countdown_timer
        remaining = COUNTDOWN_SECONDS - int(elapsed)

        ui.draw_countdown(frame, current_employee, remaining, elapsed, COUNTDOWN_SECONDS)

        # Transition
        if elapsed >= COUNTDOWN_SECONDS:
            STATE = "CHECKING"
            print(f"[Main] Countdown done → Starting PPE check for {current_employee['name']}")

            # ══════════════════════════════════════════════════════════════
    # STATE: CHECKING — QR found, now check PPE
    # ══════════════════════════════════════════════════════════════
    elif STATE == "CHECKING":

        # Show checking banner
        ui.draw_checking_banner(frame, current_employee['name'],
                                ppe_check_frames, PPE_FRAMES_NEEDED, bar_h)

        # Reuse cached detections from the multi-person overlay
        # instead of running detector.detect() again (halves GPU cost).
        detections = cached_detections if cached_detections else detector.detect(frame)
        compliance = detector.check_ppe_compliance(detections)
        if DRAW_DETECTOR_BOXES:
            frame = detector.draw_boxes(frame, detections)

        # Collect result
        ppe_results_pool.append(compliance)
        ppe_check_frames += 1

        # After enough frames, make final decision
        if ppe_check_frames >= PPE_FRAMES_NEEDED:

            # Majority vote across collected frames
            helmet_votes  = sum(1 for r in ppe_results_pool if r["has_helmet"])
            vest_votes    = sum(1 for r in ppe_results_pool if r["has_vest"])
            gloves_votes  = sum(1 for r in ppe_results_pool if r.get("has_gloves"))
            goggles_votes = sum(1 for r in ppe_results_pool if r.get("has_goggles"))
            boots_votes   = sum(1 for r in ppe_results_pool if r.get("has_boots"))

            half = PPE_FRAMES_NEEDED // 2
            goggles_threshold = max(3, PPE_FRAMES_NEEDED // 3)
            final_compliance = {
                "has_helmet":  helmet_votes  >= half,
                "has_vest":    vest_votes    >= half,
                "has_gloves":  gloves_votes  >= half,
                "has_goggles": goggles_votes >= goggles_threshold,
                "has_boots":   boots_votes   >= half,
                "missing":     []
            }
            if not final_compliance["has_helmet"]:
                final_compliance["missing"].append("Helmet")
            if not final_compliance["has_vest"]:
                final_compliance["missing"].append("Safety Vest")
            if not final_compliance["has_gloves"]:
                final_compliance["missing"].append("Gloves")
            if not final_compliance["has_goggles"]:
                final_compliance["missing"].append("Goggles")
            if not final_compliance["has_boots"]:
                final_compliance["missing"].append("Boots")

            # Evaluate final status
            current_status = safety.evaluate(final_compliance)

            # Save to Excel
            reporter.update_employee(current_employee, current_status)
            # Send to backend
            reporter_backend.send_check_result(current_employee, current_status, camera_id=CAMERA_ID)

            result_timer = time.time()
            STATE = "DISPLAYING"
            print(f"[Main] Result → {current_status['status']}")
            
    # ══════════════════════════════════════════════════════════════
    # STATE: DISPLAYING — Show result, then reset
    # ══════════════════════════════════════════════════════════════
    elif STATE == "DISPLAYING":

        # Draw modern result overlay
        frame = ui.draw_result_overlay(frame, current_status, current_employee)

        # Countdown timer
        elapsed   = time.time() - result_timer
        remaining = int(RESULT_DISPLAY_SECONDS - elapsed)

        ui.draw_next_check_timer(frame, remaining)
        ui.draw_saved_confirmation(frame)

        # Auto reset after display time
        if elapsed >= RESULT_DISPLAY_SECONDS:
            STATE = "SCANNING"
            scanner.reset()
            current_employee = None
            current_status   = None
            print("\n[Main] Ready for next worker...\n" + "-"*55)

    # ── Show frame ─────────────────────────────────────────────────
    cv2.imshow("Industriguard-AI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n[Main] Shutting down...")
        break

camera.release()
print("[Main] System stopped.\n")