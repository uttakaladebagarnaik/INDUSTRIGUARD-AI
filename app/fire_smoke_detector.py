from ultralytics import YOLO


class FireSmokeDetector:

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, frame, confidence=0.20):

        results = self.model(
            frame,
            conf=confidence,
            device=0,
            verbose=False
        )

        detections = []

        for box in results[0].boxes:

            class_id = int(box.cls[0])
            confidence_score = float(box.conf[0])

            class_name = self.model.names[class_id]

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            detections.append({
                "class": class_name,
                "confidence": round(confidence_score, 3),
                "bbox": [x1, y1, x2, y2]
            })

        return detections