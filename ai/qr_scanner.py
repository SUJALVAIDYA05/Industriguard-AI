import cv2
import json
import os
from pyzbar import pyzbar

class QRScanner:
    def __init__(self, employees_file="employee_data/employees.json"):
        self.employees_file = employees_file
        self.employee_db    = self._load_employees()

        # Tracks current scanned employee
        # Stays set until a new QR is scanned
        self.current_employee = None
        self.scan_confirmed   = False

        print(f"[QRScanner] Loaded {len(self.employee_db)} employees from database")

    def _load_employees(self):
        """
        Loads employees.json and builds a lookup dictionary.
        Key = Employee ID, Value = employee details dict
        """
        if not os.path.exists(self.employees_file):
            print(f"[QRScanner] WARNING: {self.employees_file} not found")
            return {}

        with open(self.employees_file, "r") as f:
            data = json.load(f)

        # Build lookup dict: {"EMP-001": {...}, "EMP-002": {...}}
        return {emp["id"]: emp for emp in data["employees"]}

    def scan_frame(self, frame):
        """
        Scans a single frame for QR codes.
        Returns employee dict if valid QR found, None otherwise.
        """
        # Decode all QR codes in the frame
        qr_codes = pyzbar.decode(frame)

        for qr in qr_codes:
            # Get the raw text data from QR
            raw_data = qr.data.decode("utf-8").strip()
            print(f"[QRScanner] QR Detected: {raw_data}")

            # Check if this QR matches an employee ID
            if raw_data in self.employee_db:
                employee = self.employee_db[raw_data]
                self.current_employee = employee
                self.scan_confirmed   = True
                print(f"[QRScanner] Employee Identified: "
                      f"{employee['id']} — {employee['name']}")
                return employee
            else:
                print(f"[QRScanner] Unknown QR code: {raw_data}")
                return None

        # No QR code found in this frame
        return None

    def draw_qr_overlay(self, frame, detected_employee):
        """
        Draws a box around the detected QR code
        and shows employee info on screen.
        """
        qr_codes = pyzbar.decode(frame)

        for qr in qr_codes:
            # Draw box around QR code
            points = qr.polygon
            if len(points) == 4:
                pts = [(p.x, p.y) for p in points]
                for i in range(4):
                    cv2.line(
                        frame,
                        pts[i],
                        pts[(i + 1) % 4],
                        (0, 255, 0), 3
                    )

            # Show employee name above QR box
            if detected_employee:
                x = qr.rect.left
                y = qr.rect.top - 10

                cv2.putText(
                    frame,
                    f"{detected_employee['id']} — {detected_employee['name']}",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2
                )

        return frame

    def reset(self):
        """Call this after a check is complete to allow next employee"""
        self.current_employee = None
        self.scan_confirmed   = False