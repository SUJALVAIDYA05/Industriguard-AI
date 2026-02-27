from ultralytics import YOLO
import cv2

class PPEDetector:
    def __init__(self, model_path="yolov8n.pt"):
        self.model = YOLO(model_path)
        print(f"[PPEDetector] Model loaded → {model_path}")

        # Update these class names once you have a trained PPE model
        self.HELMET_CLASSES  = ["helmet", "hard hat", "hardhat"]
        self.VEST_CLASSES    = ["vest", "safety vest", "reflective vest"]

    def detect(self, frame):
        """Runs detection and returns list of detected objects"""
        results     = self.model(frame, verbose=False)
        detections  = []

        for result in results:
            for box in result.boxes:
                class_id    = int(box.cls[0])
                confidence  = float(box.conf[0])
                class_name  = self.model.names[class_id]
                bbox        = box.xyxy[0].tolist()

                detections.append({
                    "class_id":   class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox":       [int(b) for b in bbox]
                })

        return detections

    def check_ppe_compliance(self, detections):
        """
        Checks helmet and vest presence.
        Returns simple compliance dict.
        """
        detected_names = " ".join(
            [d["class_name"].lower() for d in detections]
        )

        has_helmet = any(
            word in detected_names
            for word in self.HELMET_CLASSES
        )
        has_vest = any(
            word in detected_names
            for word in self.VEST_CLASSES
        )

        missing = []
        if not has_helmet:
            missing.append("Helmet")
        if not has_vest:
            missing.append("Safety Vest")

        return {
            "has_helmet": has_helmet,
            "has_vest":   has_vest,
            "missing":    missing
        }

    def draw_boxes(self, frame, detections):
        """Draws detection boxes on frame"""
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f'{det["class_name"]} {det["confidence"]}'

            is_violation = any(
                word in det["class_name"].lower()
                for word in ["no_helmet", "no_vest", "no helmet", "no vest"]
            )
            color = (0, 0, 255) if is_violation else (0, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, color, 2
            )

        return frame