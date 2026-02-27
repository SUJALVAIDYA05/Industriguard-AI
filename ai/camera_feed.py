import cv2

class CameraFeed:
    def __init__(self, source=None):
        """
        source = None        → auto detect (tries mobile first, falls back to webcam)
        source = 0           → laptop webcam
        source = "http://192.168.x.x:8080/video" → mobile camera via IP Webcam app
        source = "video.mp4" → recorded video for testing
        """
        if source is None:
            source = 0  # Default to webcam

        self.source = source
        self.cap = cv2.VideoCapture(source)

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"[CameraFeed] Cannot open source: {source}\n"
                f"  If using mobile, check:\n"
                f"  1. Phone and laptop on same WiFi\n"
                f"  2. IP Webcam app is running on phone\n"
                f"  3. URL is correct"
            )

        print(f"[CameraFeed] Camera opened → source: {source}")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
        print("[CameraFeed] Camera released")