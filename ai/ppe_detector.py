from ultralytics import YOLO
import cv2

class PPEDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """
        For now we use yolov8n.pt (general model) to verify everything works.
        Later we replace this with our trained PPE model.
        """
        self.model = YOLO(model_path)
        print(f"[PPEDetector] Model loaded → {model_path}")

        # These will be updated once we have a real PPE trained model
        # For the general yolov8n model, class 0 = person
        self.PPE_CLASSES = {
            "helmet": ["helmet", "hard hat", "hardhat"],
            "vest": ["vest", "safety vest", "reflective vest"]
        }

    def detect(self, frame):
        """
        Run detection on a single frame.
        Returns list of detected objects with class, confidence, bbox.
        """
        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox": [int(b) for b in bbox]
                })

        return detections

    def draw_boxes(self, frame, detections):
        """
        Draws bounding boxes on the frame for visualization.
        Green = safe / detected
        Red = violation
        """
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f'{det["class_name"]} {det["confidence"]}'

            # Color based on class (customize once PPE model is ready)
            color = (0, 255, 0)  # Green by default

            if any(word in det["class_name"].lower() 
                   for word in ["no_helmet", "no_vest", "no helmet", "no vest"]):
                color = (0, 0, 255)  # Red for violations

            # Draw rectangle and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, color, 2
            )

        return frame

    def check_ppe_compliance(self, detections):
        """
        Checks if required PPE is detected.
        Returns compliance status dict.
        This logic will be refined once we have a trained PPE model.
        """
        detected_classes = [d["class_name"].lower() for d in detections]

        has_helmet = any(
            helmet_word in " ".join(detected_classes)
            for helmet_word in self.PPE_CLASSES["helmet"]
        )
        has_vest = any(
            vest_word in " ".join(detected_classes)
            for vest_word in self.PPE_CLASSES["vest"]
        )

        return {
            "has_helmet": has_helmet,
            "has_vest": has_vest,
            "missing": [
                item for item, present in
                [("Helmet", has_helmet), ("Safety Vest", has_vest)]
                if not present
            ]
        }