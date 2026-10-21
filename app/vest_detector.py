from ultralytics import YOLO


class VestDetector:

    def __init__(self, model_path):
        print("Loading PPE model...")
        self.model = YOLO(model_path)

        print("PPE classes:")
        print(self.model.names)

    def detect(self, frame, confidence=0.10):

        results = self.model(
            frame,
            conf=confidence,
            imgsz=960,
            iou=0.45,
            max_det=30,
            verbose=False
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        for box in result.boxes:

            class_id = int(box.cls[0])
            score = float(box.conf[0])

            class_name = self.model.names[class_id]

            # We only want safety vest
            if class_name != "safety_vest":
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            detections.append({
                "class": "safety_vest",
                "confidence": round(score, 3),
                "bbox": [x1, y1, x2, y2]
            })

        return detections