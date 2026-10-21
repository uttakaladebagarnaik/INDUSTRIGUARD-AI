class PersonPPEAssociator:

    def center(self, box):
        x1, y1, x2, y2 = box
        return (
            (x1 + x2) / 2,
            (y1 + y2) / 2
        )

    def associate(self, persons, ppe_detections):

        workers = []

        for index, person in enumerate(persons, start=1):

            x1, y1, x2, y2 = person["bbox"]

            width = x2 - x1
            height = y2 - y1

            worker = {
                "worker_id": index,
                "track_id": person.get("track_id", -1),

                "person_bbox": [
                    x1, y1, x2, y2
                ],

                "helmet": "UNKNOWN",
                "helmet_confidence": 0.0,

                "vest": "UNKNOWN",
                "vest_confidence": 0.0
            }

            # ==========================================
            # HEAD REGION
            # ==========================================

            head_x1 = x1 - int(width * 0.20)
            head_x2 = x2 + int(width * 0.20)

            head_y1 = y1
            head_y2 = y1 + int(height * 0.40)

            # ==========================================
            # TORSO REGION
            # ==========================================

            torso_x1 = x1
            torso_x2 = x2

            torso_y1 = y1 + int(height * 0.20)
            torso_y2 = y1 + int(height * 0.90)

            # ==========================================
            # HELMET DETECTION
            # ==========================================

            helmet_candidates = []

            for detection in ppe_detections:

                class_name = detection["class"]

                if class_name not in [
                    "helmet",
                    "no_helmet"
                ]:
                    continue

                cx, cy = self.center(
                    detection["bbox"]
                )

                if (
                    head_x1 <= cx <= head_x2
                    and
                    head_y1 <= cy <= head_y2
                ):
                    helmet_candidates.append(
                        detection
                    )

            if helmet_candidates:

                helmet_candidates.sort(
                    key=lambda d: d["confidence"],
                    reverse=True
                )

                best_helmet = helmet_candidates[0]

                worker["helmet"] = best_helmet["class"]

                worker["helmet_confidence"] = (
                    best_helmet["confidence"]
                )

            # ==========================================
            # SAFETY VEST DETECTION
            # ==========================================

            vest_candidates = []

            for detection in ppe_detections:

                if detection["class"] != "safety_vest":
                    continue

                cx, cy = self.center(
                    detection["bbox"]
                )

                if (
                    torso_x1 <= cx <= torso_x2
                    and
                    torso_y1 <= cy <= torso_y2
                ):
                    vest_candidates.append(
                        detection
                    )

            if vest_candidates:

                best_vest = max(
                    vest_candidates,
                    key=lambda d: d["confidence"]
                )

                worker["vest"] = "safety_vest"

                worker["vest_confidence"] = (
                    best_vest["confidence"]
                )

            workers.append(worker)

        return workers