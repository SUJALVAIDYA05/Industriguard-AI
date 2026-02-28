"""
Run this script to diagnose mobile camera connection issues.
Usage: python diagnose_camera.py
"""
import cv2
import urllib.request
import socket
from config import CAMERA_SOURCE

def check_network():
    print("\n── Network Check ─────────────────────────────")
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"   Laptop hostname : {hostname}")
    print(f"   Laptop IP       : {local_ip}")

def check_url_reachable(url):
    print("\n── URL Reachability Check ────────────────────")
    print(f"   Testing: {url}")
    try:
        urllib.request.urlopen(url, timeout=5)
        print("   ✅ URL is reachable")
        return True
    except Exception as e:
        print(f"   ❌ URL not reachable: {e}")
        print("\n   Possible fixes:")
        print("   → Make sure IP Webcam app is running on phone")
        print("   → Make sure phone and laptop are on same WiFi")
        print("   → Check IP address in config.py")
        return False

def check_opencv_connection(url):
    print("\n── OpenCV Connection Check ───────────────────")
    print(f"   Connecting via OpenCV to: {url}")
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("   ❌ OpenCV cannot open stream")
        return False

    ret, frame = cap.read()
    if not ret:
        print("   ❌ OpenCV opened but cannot read frames")
        cap.release()
        return False

    h, w = frame.shape[:2]
    print(f"   ✅ OpenCV connected successfully")
    print(f"   ✅ Frame size: {w}x{h}")
    cap.release()
    return True

def run_diagnostics():
    print("\n" + "="*50)
    print("  IndustriGuard Camera Diagnostics")
    print("="*50)

    print(f"\n   Configured source: {CAMERA_SOURCE}")

    if not isinstance(CAMERA_SOURCE, str):
        print("   Using webcam (source=0) — no network needed")
        return

    # Extract base URL for reachability check
    parts    = CAMERA_SOURCE.split("/")
    base_url = "/".join(parts[:3])  # http://192.168.x.x:8080

    check_network()
    url_ok = check_url_reachable(base_url)

    if url_ok:
        check_opencv_connection(CAMERA_SOURCE)

    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    run_diagnostics()