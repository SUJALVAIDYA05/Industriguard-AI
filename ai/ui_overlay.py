"""
ui_overlay.py  —  Modern, aesthetic OpenCV overlay system for IndustriGuard-AI

Uses PIL/Pillow for crisp TrueType font rendering (Segoe UI) instead of
OpenCV's blocky built-in fonts.  All drawing helpers live here so
main_ai.py stays clean.
"""

import cv2
import numpy as np
import math
import time
from PIL import Image, ImageDraw, ImageFont

# ── Font setup ─────────────────────────────────────────────────────────
_FONT_DIR = r"C:\Windows\Fonts"
_font_cache = {}

def _font(size, weight="regular"):
    """Load & cache a Segoe UI TrueType font at the given pixel size."""
    key = (size, weight)
    if key not in _font_cache:
        paths = {
            "light":    f"{_FONT_DIR}\\segoeuil.ttf",
            "regular":  f"{_FONT_DIR}\\segoeui.ttf",
            "semibold": f"{_FONT_DIR}\\segoeuisl.ttf",
            "bold":     f"{_FONT_DIR}\\segoeuib.ttf",
        }
        try:
            _font_cache[key] = ImageFont.truetype(paths.get(weight, paths["regular"]), size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def _pil_text_size(text, font):
    """Get (width, height) of text rendered with the given PIL font."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _put_text(img, text, pos, font_size=18, color=(245, 245, 250),
              weight="regular", anchor=None, shadow=False):
    """
    Render anti-aliased TrueType text onto an OpenCV BGR frame.
    `color` is BGR.  `pos` is (x, y) of the top-left of the text.
    `anchor` can be "center" to center text horizontally at pos[0].
    Uses a small cropped region for performance.
    """
    pil_font = _font(font_size, weight)
    tw, th = _pil_text_size(text, pil_font)
    # Add padding for descenders, shadow, and anti-aliasing
    pad = max(6, font_size // 3)
    region_w = tw + pad * 2
    region_h = th + pad * 2

    x, y = pos
    if anchor == "center":
        x = x - tw // 2

    h_frame, w_frame = img.shape[:2]

    # Create a small RGBA image for just the text
    txt_img = Image.new("RGBA", (region_w, region_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_img)
    rgb = (color[2], color[1], color[0])

    tx_local, ty_local = pad, pad
    if shadow:
        draw.text((tx_local + 1, ty_local + 1), text, font=pil_font, fill=(0, 0, 0, 100))
    draw.text((tx_local, ty_local), text, font=pil_font, fill=(*rgb, 255))

    # Compute paste coordinates on the frame
    paste_x = x - pad
    paste_y = y - pad

    # Clip to frame boundaries
    src_x1 = max(0, -paste_x)
    src_y1 = max(0, -paste_y)
    dst_x1 = max(0, paste_x)
    dst_y1 = max(0, paste_y)
    dst_x2 = min(w_frame, paste_x + region_w)
    dst_y2 = min(h_frame, paste_y + region_h)
    src_x2 = src_x1 + (dst_x2 - dst_x1)
    src_y2 = src_y1 + (dst_y2 - dst_y1)

    if dst_x2 <= dst_x1 or dst_y2 <= dst_y1:
        return

    txt_np = np.array(txt_img)
    region = txt_np[src_y1:src_y2, src_x1:src_x2]
    alpha = region[:, :, 3].astype(np.float32) / 255.0
    mask = alpha > 0

    if not np.any(mask):
        return

    roi = img[dst_y1:dst_y2, dst_x1:dst_x2]
    for c in range(3):
        ch = 2 - c  # RGBA -> BGR
        roi[:, :, c][mask] = (
            region[:, :, ch][mask] * alpha[mask] +
            roi[:, :, c][mask] * (1 - alpha[mask])
        ).astype(np.uint8)


def _put_text_get_width(img, text, pos, font_size=18, color=(245, 245, 250),
                         weight="regular", shadow=False):
    """Render text and return the rendered width in pixels."""
    pil_font = _font(font_size, weight)
    tw, _ = _pil_text_size(text, pil_font)
    _put_text(img, text, pos, font_size, color, weight, shadow=shadow)
    return tw


# ── Colour palette (BGR) ──────────────────────────────────────────────
DARK_BG       = (18, 18, 28)
CARD_BG       = (30, 30, 45)
ACCENT_BLUE   = (230, 160, 40)    # warm teal-blue
ACCENT_CYAN   = (220, 200, 60)    # cyan
ACCENT_GREEN  = (100, 220, 60)
ACCENT_RED    = (80, 60, 230)
TEXT_WHITE     = (245, 245, 250)
TEXT_DIM       = (160, 160, 175)
TEXT_MUTED     = (110, 110, 130)
DIVIDER        = (60, 60, 80)
BANNER_TOP     = (50, 40, 15)     # deep navy
BANNER_BOT     = (80, 60, 25)     # slightly lighter


# ── Helpers ────────────────────────────────────────────────────────────

def _rounded_rect(img, pt1, pt2, color, radius=12, thickness=-1):
    """Draw a rectangle with rounded corners."""
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        cv2.rectangle(img, pt1, pt2, color, thickness)
        return
    if thickness == -1:
        cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, -1)
        cv2.circle(img, (x1 + r, y1 + r), r, color, -1)
        cv2.circle(img, (x2 - r, y1 + r), r, color, -1)
        cv2.circle(img, (x1 + r, y2 - r), r, color, -1)
        cv2.circle(img, (x2 - r, y2 - r), r, color, -1)
    else:
        cv2.line(img, (x1 + r, y1), (x2 - r, y1), color, thickness)
        cv2.line(img, (x1 + r, y2), (x2 - r, y2), color, thickness)
        cv2.line(img, (x1, y1 + r), (x1, y2 - r), color, thickness)
        cv2.line(img, (x2, y1 + r), (x2, y2 - r), color, thickness)
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90,  0, 90, color, thickness)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0,   0, 90, color, thickness)


def _glass_rect(img, pt1, pt2, alpha=0.70, color=CARD_BG, radius=12):
    """Semi-transparent rounded rectangle (glass-morphism)."""
    overlay = img.copy()
    _rounded_rect(overlay, pt1, pt2, color, radius, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def _pill_badge(img, text, center, color, font_size=14, pad_x=14, pad_y=5):
    """Draw a small rounded pill-shaped badge with text."""
    pil_font = _font(font_size, "semibold")
    tw, th = _pil_text_size(text, pil_font)
    x1 = center[0] - tw // 2 - pad_x
    y1 = center[1] - th // 2 - pad_y
    x2 = center[0] + tw // 2 + pad_x
    y2 = center[1] + th // 2 + pad_y
    r = (y2 - y1) // 2
    _rounded_rect(img, (x1, y1), (x2, y2), color, r, -1)
    _put_text(img, text, (center[0], y1 + pad_y - 2), font_size, TEXT_WHITE,
              weight="semibold", anchor="center")


def _gradient_bar(img, pt1, pt2, color_left, color_right):
    """Draw a horizontal gradient rectangle."""
    x1, y1 = pt1
    x2, y2 = pt2
    width = x2 - x1
    if width <= 0:
        return
    for i in range(width):
        t = i / float(width)
        c = tuple(int(color_left[j] + t * (color_right[j] - color_left[j])) for j in range(3))
        cv2.line(img, (x1 + i, y1), (x1 + i, y2), c, 1)


def _centered_text(img, text, y, font_size=18, color=TEXT_WHITE, weight="regular"):
    """Put text centered horizontally on the frame."""
    w = img.shape[1]
    _put_text(img, text, (w // 2, y), font_size, color, weight, anchor="center")


# ── Public drawing functions ──────────────────────────────────────────

def draw_top_banner(frame, title="Industriguard-AI", subtitle="Show your ID to start the scan"):
    """
    Sleek gradient top banner with brand name + instruction.
    """
    h, w = frame.shape[:2]
    bar_h = 52

    # Gradient background
    _gradient_bar(frame, (0, 0), (w, bar_h), BANNER_TOP, BANNER_BOT)

    # Thin accent line at bottom of banner
    cv2.line(frame, (0, bar_h), (w, bar_h), ACCENT_CYAN, 2)

    # Brand name — bold
    title_w = _put_text_get_width(
        frame, title, (18, 14), font_size=22, color=TEXT_WHITE,
        weight="bold", shadow=True
    )

    # Vertical separator dot
    sep_x = 18 + title_w + 16
    cv2.circle(frame, (sep_x, 28), 3, ACCENT_CYAN, -1)

    # Subtitle — light weight
    _put_text(frame, subtitle, (sep_x + 16, 17), font_size=17,
              color=TEXT_DIM, weight="light")

    return bar_h


def draw_scanning_state(frame, bar_h):
    """
    Subtle pulsing scan indicator when waiting for QR.
    """
    h, w = frame.shape[:2]
    pulse = (math.sin(time.time() * 4) + 1) / 2.0
    radius = int(5 + 3 * pulse)
    brightness = int(150 + 105 * pulse)
    dot_color = (brightness, brightness, 60)

    y_center = bar_h + 22
    cv2.circle(frame, (24, y_center), radius, dot_color, -1)
    _put_text(frame, "Scanning for QR ID...", (42, y_center - 9),
              font_size=15, color=TEXT_DIM, weight="regular")


def draw_worker_info_card(frame, lines, bbox, color, w, h):
    """
    Modern floating info card next to a person bounding box.
    Uses glassmorphism + accent border.
    """
    x1, y1, x2, y2 = bbox
    pil_font = _font(15, "regular")
    pil_font_bold = _font(15, "semibold")
    pad_x = 12
    pad_y = 10
    line_h = 22

    # Measure widths
    max_w = 0
    for i, line in enumerate(lines):
        f = pil_font_bold if i == 0 else pil_font
        tw, _ = _pil_text_size(line, f)
        max_w = max(max_w, tw)

    box_w = max_w + pad_x * 2
    box_h = line_h * len(lines) + pad_y * 2

    # Position to the right, fallback left
    bx1 = x2 + 8
    by1 = y1
    if bx1 + box_w > (w - 10):
        bx1 = max(10, x1 - 8 - box_w)
    by1 = min(max(10, by1), max(10, h - 10 - box_h))
    bx2 = bx1 + box_w
    by2 = by1 + box_h

    # Glass background
    _glass_rect(frame, (bx1, by1), (bx2, by2), alpha=0.78, color=CARD_BG, radius=8)
    # Accent left border stripe
    cv2.line(frame, (bx1, by1 + 4), (bx1, by2 - 4), color, 3)

    # Text lines
    ty = by1 + pad_y
    for i, line in enumerate(lines):
        c = TEXT_WHITE if i == 0 else TEXT_DIM
        wt = "semibold" if i == 0 else "regular"
        _put_text(frame, line, (bx1 + pad_x, ty), font_size=15, color=c, weight=wt)
        ty += line_h


def draw_person_bbox(frame, bbox, color, is_identified=False):
    """
    Modern bounding box with corner accents instead of full rectangle.
    """
    x1, y1, x2, y2 = bbox
    bw = x2 - x1
    bh = y2 - y1
    corner_len = min(25, bw // 4, bh // 4)
    t = 3

    if is_identified:
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, 0.07, frame, 0.93, 0, frame)

    # Four L-shaped corner brackets
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, t)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, t)
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, t)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, t)
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, t)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, t)
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, t)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, t)

    # Thin connecting lines
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)


def draw_countdown(frame, employee, remaining, elapsed, total_seconds):
    """
    Modern countdown overlay with ring progress indicator.
    """
    h, w = frame.shape[:2]

    # Full-screen dark overlay
    _glass_rect(frame, (0, 52), (w, h), alpha=0.55, color=DARK_BG, radius=0)

    # Employee welcome card
    card_w = min(500, w - 40)
    card_x = (w - card_w) // 2
    card_y = 70
    card_h = 62
    _glass_rect(frame, (card_x, card_y), (card_x + card_w, card_y + card_h),
                alpha=0.80, color=CARD_BG, radius=10)
    cv2.line(frame, (card_x + 10, card_y), (card_x + card_w - 10, card_y), ACCENT_CYAN, 2)

    _centered_text(frame, f"Welcome, {employee['name']}", card_y + 12,
                   font_size=20, color=TEXT_WHITE, weight="semibold")
    dept_text = f"{employee.get('department', '')}  |  {employee.get('id', '')}"
    _centered_text(frame, dept_text, card_y + 38,
                   font_size=14, color=TEXT_MUTED, weight="light")

    # Ring progress
    cx, cy = w // 2, h // 2
    progress = min(elapsed / total_seconds, 1.0)
    angle = int(360 * progress)

    cv2.circle(frame, (cx, cy), 80, DIVIDER, 3)
    cv2.ellipse(frame, (cx, cy), (80, 80), -90, 0, angle, ACCENT_CYAN, 4)
    cv2.circle(frame, (cx, cy), 68, (40, 40, 55), 1)

    # Countdown number
    if remaining > 0:
        count_text = str(remaining)
        fs = 64
    else:
        count_text = "GO"
        fs = 42

    _put_text(frame, count_text, (cx, cy - fs // 2 + 4), font_size=fs,
              color=ACCENT_CYAN, weight="bold", anchor="center", shadow=True)

    # Message below ring
    if remaining > 0:
        msg = f"PPE scan begins in {remaining} second{'s' if remaining != 1 else ''}"
    else:
        msg = "Stand still for PPE scan"
    _centered_text(frame, msg, cy + 100, font_size=17, color=TEXT_DIM, weight="regular")

    # Bottom progress bar
    bar_y = h - 6
    bar_fill = int(w * progress)
    cv2.rectangle(frame, (0, bar_y), (w, h), DARK_BG, -1)
    if bar_fill > 0:
        _gradient_bar(frame, (0, bar_y), (bar_fill, h), ACCENT_BLUE, ACCENT_CYAN)


def draw_checking_banner(frame, employee_name, current_frame, total_frames, bar_h=52):
    """
    Sleek PPE-checking progress banner below the main header.
    """
    h, w = frame.shape[:2]
    banner_y = bar_h + 2
    banner_h = 40

    _glass_rect(frame, (0, banner_y), (w, banner_y + banner_h),
                alpha=0.82, color=(25, 55, 25), radius=0)

    _put_text(frame, f"Checking PPE for: {employee_name}",
              (18, banner_y + 10), font_size=16, color=ACCENT_GREEN, weight="semibold")

    # Progress pill on right
    prog_text = f"{current_frame}/{total_frames}"
    _pill_badge(frame, prog_text,
                (w - 60, banner_y + banner_h // 2),
                (40, 80, 40), font_size=13)


def draw_result_overlay(frame, status_data, employee):
    """
    Modern PPE result display with card layout and status badge.
    """
    h, w = frame.shape[:2]
    is_ready = status_data["status"] == "READY"
    accent = ACCENT_GREEN if is_ready else ACCENT_RED

    # Central card
    card_w = min(420, w - 60)
    card_h = 390
    cx = (w - card_w) // 2
    cy = 65

    _glass_rect(frame, (cx, cy), (cx + card_w, cy + card_h),
                alpha=0.85, color=CARD_BG, radius=14)
    _rounded_rect(frame, (cx, cy), (cx + card_w, cy + 4), accent, radius=2, thickness=-1)

    # Employee info
    name = employee["name"] if employee else "Unknown"
    emp_id = employee["id"] if employee else "---"
    dept = employee.get("department", "") if employee else ""

    info_y = cy + 14
    _centered_text(frame, f"{name}  |  {emp_id}  |  {dept}",
                   info_y, font_size=15, color=TEXT_DIM, weight="regular")

    # PPE items table
    items = [
        ("Helmet",      status_data.get("has_helmet", False)),
        ("Safety Vest", status_data.get("has_vest",   False)),
        ("Gloves",      status_data.get("has_gloves", False)),
        ("Goggles",     status_data.get("has_goggles", False)),
        ("Boots",       status_data.get("has_boots",  False)),
    ]

    row_y = info_y + 28
    row_h = 36
    table_w = card_w - 40
    table_x = cx + 20

    # Table header
    _put_text(frame, "PPE Item", (table_x + 10, row_y),
              font_size=13, color=TEXT_MUTED, weight="semibold")
    _put_text(frame, "Status", (table_x + table_w - 80, row_y),
              font_size=13, color=TEXT_MUTED, weight="semibold")
    row_y += 22
    cv2.line(frame, (table_x, row_y), (table_x + table_w, row_y), DIVIDER, 1)

    for item_name, detected in items:
        ry = row_y + 5
        row_color = (25, 50, 25) if detected else (50, 25, 25)
        _glass_rect(frame, (table_x, ry), (table_x + table_w, ry + row_h - 4),
                    alpha=0.5, color=row_color, radius=6)

        _put_text(frame, item_name, (table_x + 12, ry + 8),
                  font_size=15, color=TEXT_WHITE, weight="regular")

        if detected:
            _pill_badge(frame, "YES",
                        (table_x + table_w - 40, ry + row_h // 2 - 2),
                        (40, 110, 40), font_size=12)
        else:
            _pill_badge(frame, "NO",
                        (table_x + table_w - 40, ry + row_h // 2 - 2),
                        (60, 30, 130), font_size=12)

        row_y += row_h

    # Big status badge
    status_y = row_y + 22
    _pill_badge(frame, status_data["status"],
                (w // 2, status_y + 10), accent, font_size=22, pad_x=30, pad_y=8)

    # Message
    msg = status_data["message"]
    _centered_text(frame, msg, status_y + 42, font_size=15, color=TEXT_DIM, weight="light")

    return frame


def draw_next_check_timer(frame, remaining):
    """Small timer in the top-right area."""
    h, w = frame.shape[:2]
    text = f"Next scan in {remaining}s"
    pil_font = _font(14, "light")
    tw, _ = _pil_text_size(text, pil_font)
    _put_text(frame, text, (w - tw - 18, 18), font_size=14,
              color=TEXT_MUTED, weight="light")


def draw_saved_confirmation(frame):
    """Small saved indicator at bottom-right."""
    h, w = frame.shape[:2]
    text = "Saved to report"
    pil_font = _font(14, "regular")
    tw, _ = _pil_text_size(text, pil_font)
    x = w - tw - 30
    y = h - 26
    cv2.circle(frame, (x - 8, y + 6), 4, ACCENT_GREEN, -1)
    _put_text(frame, text, (x, y), font_size=14, color=ACCENT_GREEN, weight="regular")
