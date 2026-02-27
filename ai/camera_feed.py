import cv2

class CameraFeed:
    def __init__(self, source="http://192.168.0.101:8080/video"):
        """
        source=0 means your laptop/PC webcam
        source="rtsp://192.168.x.x/..." means IP/CCTV camera
        source="video.mp4" means a recorded video file (good for testing)
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)

        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera source: {source}")
        
        print(f"[CameraFeed] Camera opened successfully → source: {source}")

    def get_frame(self):
        """Returns a single frame from the camera"""
        ret, frame = self.cap.read()
        if not ret:
            print("[CameraFeed] Warning: Could not read frame")
            return None
        return frame

    def release(self):
        """Always call this when done to free the camera"""
        self.cap.release()
        cv2.destroyAllWindows()
        print("[CameraFeed] Camera released")