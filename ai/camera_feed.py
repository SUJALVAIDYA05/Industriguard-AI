import cv2
import time
from config import CAMERA_SOURCE, USE_WEBCAM_FALLBACK

class CameraFeed:
    def __init__(self, source=None):
        if source is None:
            source = 0 if USE_WEBCAM_FALLBACK else CAMERA_SOURCE

        self.source       = source
        self.is_mobile    = isinstance(source, str) and source.startswith("http")
        self.cap          = None
        self.reconnect_attempts = 0

        self._connect()

    def _connect(self):
        """Opens the camera connection"""
        print(f"[CameraFeed] Connecting to → {self.source}")

        self.cap = cv2.VideoCapture(self.source)

        if self.is_mobile:
            # Mobile streams need these buffer settings
            # to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            # Webcam resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

        if not self.cap.isOpened():
            if self.is_mobile:
                raise RuntimeError(
                    f"\n[CameraFeed] ❌ Cannot connect to mobile camera\n"
                    f"   URL: {self.source}\n\n"
                    f"   Troubleshoot:\n"
                    f"   1. Is IP Webcam app running on your phone?\n"
                    f"   2. Are phone and laptop on the same WiFi?\n"
                    f"   3. Open {self.source} in your browser first\n"
                    f"   4. Check the IP in config.py matches your phone\n"
                )
            else:
                raise RuntimeError("[CameraFeed] ❌ Cannot open webcam")

        source_type = "Mobile Camera" if self.is_mobile else "Webcam"
        print(f"[CameraFeed] ✅ Connected → {source_type}")

    def get_frame(self):
        """
        Returns a frame. Auto-reconnects if mobile stream drops.
        """
        ret, frame = self.cap.read()

        if not ret:
            if self.is_mobile:
                print("[CameraFeed] ⚠ Frame dropped — attempting reconnect...")
                time.sleep(1)
                self._connect()
                self.reconnect_attempts += 1

                if self.reconnect_attempts > 10:
                    print("[CameraFeed] ❌ Too many failed reconnects. Exiting.")
                    return None

                ret, frame = self.cap.read()
                if ret:
                    self.reconnect_attempts = 0
                    print("[CameraFeed] ✅ Reconnected successfully")
                    return frame

            return None

        self.reconnect_attempts = 0
        return frame

    def get_info(self):
        """Returns camera info for display"""
        return {
            "source": self.source,
            "type":   "Mobile" if self.is_mobile else "Webcam",
            "width":  int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps":    int(self.cap.get(cv2.CAP_PROP_FPS))
        }

    def release(self):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("[CameraFeed] Camera released")