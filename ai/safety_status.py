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
        has_gloves  = compliance.get("has_gloves", False)
        has_goggles = compliance.get("has_goggles", False)
        has_boots   = compliance.get("has_boots", False)
        missing     = compliance.get("missing", [])

        all_present = has_helmet and has_vest and has_gloves and has_goggles and has_boots

        if all_present:
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
            "has_gloves":   has_gloves,
            "has_goggles":  has_goggles,
            "has_boots":    has_boots,
            "missing":      missing,
            "message":      message,
            "color":        color
        }

    def draw_status(self, frame, status_data, employee):
        """
        Draws a PPE results table + overall status on the frame.
        Table columns: Item | Recognition
        """
        import cv2

        h, w = frame.shape[:2]
        color = status_data["color"]

        # ── PPE items table data ────────────────────────────────────
        items = [
            ("Helmet",      status_data.get("has_helmet", False)),
            ("Safety Vest", status_data.get("has_vest",   False)),
            ("Gloves",      status_data.get("has_gloves", False)),
            ("Goggles",     status_data.get("has_goggles", False)),
            ("Boots",       status_data.get("has_boots",  False)),
        ]

        # ── Table layout constants ────────────────────────────
        font       = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65
        thickness  = 2
        row_h      = 34        # height per row (compact for 5 rows)
        pad_x      = 15        # horizontal padding inside cells
        col1_w     = 180       # "Item" column width
        col2_w     = 160       # "Recognition" column width
        table_w    = col1_w + col2_w
        header_h   = 42        # header row height
        n_rows     = len(items)
        table_h    = header_h + row_h * n_rows

        # Center the table horizontally, place it in the upper-middle area
        tx = (w - table_w) // 2
        ty = 60                # top margin below the banner

        # ── Semi-transparent dark backdrop ────────────────────
        overlay = frame.copy()
        backdrop_pad = 20
        cv2.rectangle(
            overlay,
            (tx - backdrop_pad, ty - backdrop_pad),
            (tx + table_w + backdrop_pad, ty + table_h + 140 + backdrop_pad),
            (15, 15, 25), -1
        )
        cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

        # ── Table border (rounded feel via thick border) ──────
        cv2.rectangle(frame, (tx, ty), (tx + table_w, ty + table_h), (180, 180, 180), 2)

        # ── Header row ────────────────────────────────────────
        cv2.rectangle(frame, (tx, ty), (tx + table_w, ty + header_h), (50, 50, 70), -1)
        cv2.rectangle(frame, (tx, ty), (tx + table_w, ty + header_h), (180, 180, 180), 2)
        # Column divider in header
        cv2.line(frame, (tx + col1_w, ty), (tx + col1_w, ty + header_h), (180, 180, 180), 2)

        cv2.putText(frame, "PPE Item",
                    (tx + pad_x, ty + 28),
                    font, font_scale, (255, 255, 255), thickness)
        cv2.putText(frame, "Recognition",
                    (tx + col1_w + pad_x, ty + 28),
                    font, font_scale, (255, 255, 255), thickness)

        # ── Data rows ─────────────────────────────────────────
        for i, (item_name, detected) in enumerate(items):
            ry = ty + header_h + i * row_h

            # Row background — green tint if detected, red tint if missing
            if detected:
                row_bg  = (25, 60, 25)
                txt_col = (80, 255, 80)
                status_txt = "Yes"
            else:
                row_bg  = (60, 25, 25)
                txt_col = (100, 100, 255)
                status_txt = "No"

            cv2.rectangle(frame, (tx, ry), (tx + table_w, ry + row_h), row_bg, -1)
            # Row border
            cv2.rectangle(frame, (tx, ry), (tx + table_w, ry + row_h), (120, 120, 120), 1)
            # Column divider
            cv2.line(frame, (tx + col1_w, ry), (tx + col1_w, ry + row_h), (120, 120, 120), 1)

            # Item name
            cv2.putText(frame, item_name,
                        (tx + pad_x, ry + 26),
                        font, font_scale, (220, 220, 220), thickness)

            # Status icon + text
            icon = chr(10003) if detected else "X"   # checkmark or X
            cv2.putText(frame, f"{icon}  {status_txt}",
                        (tx + col1_w + pad_x, ry + 26),
                        font, font_scale, txt_col, thickness)

        # ── Overall status + employee info below table ────────
        info_y = ty + table_h + 30

        # Employee name
        name   = employee["name"] if employee else "Unknown"
        emp_id = employee["id"]   if employee else "---"
        dept   = employee.get("department", "") if employee else ""

        emp_text = f"{emp_id}  |  {name}  |  {dept}"
        emp_tw   = cv2.getTextSize(emp_text, font, 0.6, 1)[0][0]
        cv2.putText(frame, emp_text,
                    ((w - emp_tw) // 2, info_y),
                    font, 0.6, (200, 200, 220), 1)

        # Overall STATUS — large, centered, color-coded
        status_text = status_data["status"]
        s_scale     = 1.2
        s_thick     = 3
        s_tw        = cv2.getTextSize(status_text, font, s_scale, s_thick)[0][0]
        cv2.putText(frame, status_text,
                    ((w - s_tw) // 2, info_y + 45),
                    font, s_scale, color, s_thick)

        # Message (e.g. "All PPE compliant" or "Missing: Helmet")
        msg    = status_data["message"]
        msg_tw = cv2.getTextSize(msg, font, 0.55, 1)[0][0]
        cv2.putText(frame, msg,
                    ((w - msg_tw) // 2, info_y + 75),
                    font, 0.55, (180, 180, 180), 1)

        return frame