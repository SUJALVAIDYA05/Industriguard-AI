class SafetyStatus:
    def __init__(self):
        print("[SafetyStatus] Safety Status Engine initialized")

    def evaluate(self, compliance):
        """
        Simple rule:
        ALL required PPE present → READY
        ANY PPE missing          → NOT READY

        Returns status dict.
        """
        has_helmet  = compliance.get("has_helmet", False)
        has_vest    = compliance.get("has_vest", False)
        missing     = compliance.get("missing", [])

        if has_helmet and has_vest:
            status  = "READY"
            color   = (0, 200, 0)    # Green
            message = "All PPE compliant. Safe to enter."
        else:
            status  = "NOT READY"
            color   = (0, 0, 255)    # Red
            missing_str = ", ".join(missing)
            message = f"Missing PPE: {missing_str}"

        return {
            "status":       status,
            "has_helmet":   has_helmet,
            "has_vest":     has_vest,
            "missing":      missing,
            "message":      message,
            "color":        color
        }

    def draw_status(self, frame, status_data, employee):
        """
        Draws the final status banner on the frame.
        Shows employee name + READY / NOT READY.
        """
        import cv2

        h, w = frame.shape[:2]
        color = status_data["color"]

        # Bottom banner
        cv2.rectangle(
            frame,
            (0, h - 100),
            (w, h),
            color, -1
        )

        # Employee name
        name = employee["name"] if employee else "Unknown"
        emp_id = employee["id"] if employee else "---"

        cv2.putText(
            frame,
            f"{emp_id} — {name}",
            (15, h - 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 255), 2
        )

        # Status text
        cv2.putText(
            frame,
            f'STATUS: {status_data["status"]}',
            (15, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0, (255, 255, 255), 2
        )

        # Message (missing PPE details)
        cv2.putText(
            frame,
            status_data["message"],
            (w // 2, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65, (255, 255, 255), 1
        )

        return frame