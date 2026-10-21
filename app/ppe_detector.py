from ultralytics import YOLO


class PPEDetector:

    # ---------------------------------------------------------
    # CLASS-SPECIFIC CONFIDENCE
    # ---------------------------------------------------------
    # Do NOT treat weak no-helmet predictions as violations.
    HELMET_MIN_CONF = 0.20
    NO_HELMET_MIN_CONF = 0.35
    VEST_MIN_CONF = 0.20

    def __init__(self, model_path):

        print(f"Loading PPE model: {model_path}")

        self.model = YOLO(model_path)

        print()
        print("PPE classes:")
        print(self.model.names)
        print()

    def detect(self, frame, confidence=0.15):

        # -----------------------------------------------------
        # HIGHER RESOLUTION PPE INFERENCE
        # -----------------------------------------------------
        results = self.model(
            frame,
            conf=confidence,
            imgsz=960,
            iou=0.45,
            max_det=50,
            verbose=False
        )

        detections = []

        if not results:
            return detections

        result = results[0]

        if result.boxes is None:
            return detections

        # -----------------------------------------------------
        # PROCESS DETECTIONS
        # -----------------------------------------------------
        for box in result.boxes:

            class_id = int(box.cls[0])
            score = float(box.conf[0])

            if class_id not in self.model.names:
                continue

            class_name = self.model.names[class_id]

            # Normalize class name
            class_name = str(class_name).lower().strip()

            # -------------------------------------------------
            # CLASS-SPECIFIC THRESHOLDS
            # -------------------------------------------------

            if class_name == "helmet":

                if score < self.HELMET_MIN_CONF:
                    continue

            elif class_name == "no_helmet":

                # Weak no-helmet predictions are ignored.
                if score < self.NO_HELMET_MIN_CONF:
                    continue

            elif class_name == "safety_vest":

                if score < self.VEST_MIN_CONF:
                    continue

            else:

                # Ignore classes that are not part of our PPE system.
                continue

            # -------------------------------------------------
            # BOUNDING BOX
            # -------------------------------------------------

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            detections.append({
                "class": class_name,
                "confidence": round(score, 3),
                "bbox": [
                    x1,
                    y1,
                    x2,
                    y2
                ]
            })

        # -----------------------------------------------------
        # SORT BY CONFIDENCE
        # -----------------------------------------------------

        detections.sort(
            key=lambda detection: detection["confidence"],
            reverse=True
        )

        return detections