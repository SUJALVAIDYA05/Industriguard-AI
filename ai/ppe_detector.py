from ultralytics import YOLO
import cv2

class PPEDetector:
    # Minimum confidence to keep a detection (filters noise)
    MIN_CONFIDENCE = 0.30

    def __init__(self, model_path="ppe_model.pt"):
        self.model = YOLO(model_path)
        print(f"[PPEDetector] Model loaded → {model_path}")

        self.CLASS_CONFIDENCE = {"goggles": 0.15}

        self.HELMET_CLASSES    = ["helmet"]
        self.VEST_CLASSES      = ["vest"]
        self.GLOVES_CLASSES    = ["gloves"]
        self.GOGGLES_CLASSES   = ["goggles"]
        self.BOOTS_CLASSES     = ["boots"]
        self.PERSON_CLASSES    = ["person"]
        self.VIOLATION_CLASSES = ["no_helmet", "no_goggle", "no_gloves", "no_boots"]

    def detect(self, frame):
        """Runs detection and returns list of detected objects"""
        results     = self.model(frame, verbose=False)
        detections  = []

        for result in results:
            for box in result.boxes:
                class_id    = int(box.cls[0])
                confidence  = float(box.conf[0])
                class_name  = self.model.names[class_id]
                min_conf    = self.CLASS_CONFIDENCE.get(class_name.lower(), self.MIN_CONFIDENCE)
                if confidence < min_conf:
                    continue
                bbox        = box.xyxy[0].tolist()

                detections.append({
                    "class_id":   class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox":       [int(b) for b in bbox]
                })

        return detections

    def detect_with_tracks(self, frame, tracker="bytetrack.yaml"):
        """
        Runs detection + tracking using Ultralytics trackers (ByteTrack by default).
        Returns detections like detect(), but includes:
          - track_id (int) when available
        """
        try:
            results = self.model.track(frame, persist=True, tracker=tracker, verbose=False)
        except Exception:
            # Fallback to plain detect if track() is not supported in this env
            return self.detect(frame)

        detections = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]
                min_conf = self.CLASS_CONFIDENCE.get(class_name.lower(), self.MIN_CONFIDENCE)
                if confidence < min_conf:
                    continue
                bbox = box.xyxy[0].tolist()

                track_id = None
                try:
                    if getattr(box, "id", None) is not None:
                        track_id = int(box.id[0])
                except Exception:
                    track_id = None

                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox": [int(b) for b in bbox],
                    "track_id": track_id,
                })

        return detections

    def detect_with_tracks_fast(self, frame, tracker="bytetrack.yaml", imgsz=None):
        """
        Same as detect_with_tracks(), but allows reducing inference size via imgsz.
        """
        try:
            kwargs = {"persist": True, "tracker": tracker, "verbose": False}
            if imgsz:
                kwargs["imgsz"] = int(imgsz)
            results = self.model.track(frame, **kwargs)
        except Exception:
            return self.detect(frame)

        detections = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.model.names[class_id]
                min_conf = self.CLASS_CONFIDENCE.get(class_name.lower(), self.MIN_CONFIDENCE)
                if confidence < min_conf:
                    continue
                bbox = box.xyxy[0].tolist()

                track_id = None
                try:
                    if getattr(box, "id", None) is not None:
                        track_id = int(box.id[0])
                except Exception:
                    track_id = None

                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": round(confidence, 2),
                    "bbox": [int(b) for b in bbox],
                    "track_id": track_id,
                })

        return detections

    def _is_class(self, det, class_names):
        name = (det.get("class_name") or "").lower().strip()
        return any(name == c for c in class_names)

    def split_detections(self, detections):
        persons, helmets, vests, gloves, goggles, boots, negatives, other = [], [], [], [], [], [], [], []
        for d in detections or []:
            if self._is_class(d, self.PERSON_CLASSES):
                persons.append(d)
            elif self._is_class(d, self.HELMET_CLASSES):
                helmets.append(d)
            elif self._is_class(d, self.VEST_CLASSES):
                vests.append(d)
            elif self._is_class(d, self.GLOVES_CLASSES):
                gloves.append(d)
            elif self._is_class(d, self.GOGGLES_CLASSES):
                goggles.append(d)
            elif self._is_class(d, self.BOOTS_CLASSES):
                boots.append(d)
            elif self._is_class(d, self.VIOLATION_CLASSES):
                negatives.append(d)
            else:
                other.append(d)
        return persons, helmets, vests, gloves, goggles, boots, negatives, other

    def _center(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

    def _point_in_bbox(self, pt, bbox):
        x, y = pt
        x1, y1, x2, y2 = bbox
        return x1 <= x <= x2 and y1 <= y <= y2

    def _expand_bbox_up(self, bbox, factor=0.35):
        x1, y1, x2, y2 = bbox
        bh = y2 - y1
        return [x1, int(y1 - bh * factor), x2, y2]

    def _expand_bbox_upper_portion(self, bbox, factor=0.35):
        x1, y1, x2, y2 = bbox
        bh = y2 - y1
        return [x1, y1, x2, int(y1 + bh * factor)]

    def _expand_bbox_down(self, bbox, factor=0.20):
        """
        Expand a bounding box DOWNWARD by `factor` of its height.
        Boots are at the feet and may extend below the person bbox.
        """
        x1, y1, x2, y2 = bbox
        bh = y2 - y1
        return [x1, y1, x2, int(y2 + bh * factor)]

    def per_person_compliance(self, detections):
        persons, helmets, vests, gloves, goggles, boots, negatives, _ = self.split_detections(detections)
        out = []

        for p in persons:
            pb = p["bbox"]
            pb_up     = self._expand_bbox_up(pb, factor=0.35)
            pb_upper  = self._expand_bbox_upper_portion(pb, factor=0.35)
            pb_down   = self._expand_bbox_down(pb, factor=0.20)

            has_helmet  = any(self._point_in_bbox(self._center(h["bbox"]), pb_up) for h in helmets)
            has_vest    = any(self._point_in_bbox(self._center(v["bbox"]), pb) for v in vests)
            has_gloves  = any(self._point_in_bbox(self._center(g["bbox"]), pb) for g in gloves)
            has_goggles = any(self._point_in_bbox(self._center(g["bbox"]), pb_upper) for g in goggles)
            if not has_goggles:
                has_goggles = any(self._point_in_bbox(self._center(g["bbox"]), pb) for g in goggles)
            has_no_goggle_near = any(self._point_in_bbox(self._center(n["bbox"]), pb_upper) for n in negatives if self._is_class(n, ["no_goggle"]))
            if has_no_goggle_near:
                has_goggles = False
            has_boots   = any(self._point_in_bbox(self._center(b["bbox"]), pb_down) for b in boots)

            total_items = 5
            found = sum([has_helmet, has_vest, has_gloves, has_goggles, has_boots])
            safety_pct = int(round((found / total_items) * 100))

            out.append({
                "person_det": p,
                "has_helmet": has_helmet,
                "has_vest": has_vest,
                "has_gloves": has_gloves,
                "has_goggles": has_goggles,
                "has_boots": has_boots,
                "safety_percentage": safety_pct
            })

        return out

    def check_ppe_compliance(self, detections):
        """
        Checks all PPE item presence.
        Returns simple compliance dict.
        """
        detected_names = [d["class_name"].lower() for d in detections]

        has_helmet  = any(c in detected_names for c in self.HELMET_CLASSES)
        has_vest    = any(c in detected_names for c in self.VEST_CLASSES)
        has_gloves  = any(c in detected_names for c in self.GLOVES_CLASSES)
        has_goggles = any(c in detected_names for c in self.GOGGLES_CLASSES)
        has_boots   = any(c in detected_names for c in self.BOOTS_CLASSES)

        missing = []
        if not has_helmet:
            missing.append("Helmet")
        if not has_vest:
            missing.append("Safety Vest")
        if not has_gloves:
            missing.append("Gloves")
        if not has_goggles:
            missing.append("Goggles")
        if not has_boots:
            missing.append("Boots")

        return {
            "has_helmet":  has_helmet,
            "has_vest":    has_vest,
            "has_gloves":  has_gloves,
            "has_goggles": has_goggles,
            "has_boots":   has_boots,
            "missing":     missing
        }

    def draw_boxes(self, frame, detections):
        """Draws detection boxes on frame"""
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = f'{det["class_name"]} {det["confidence"]}'

            is_violation = self._is_class(det, self.VIOLATION_CLASSES)
            color = (0, 0, 255) if is_violation else (0, 255, 0)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame, label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, color, 2
            )

        return frame