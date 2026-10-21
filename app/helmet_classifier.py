from ultralytics import YOLO
import cv2


class HelmetClassifier:

    def __init__(self, model_path):

        print(
            f"Loading Helmet Classifier: {model_path}"
        )

        self.model = YOLO(model_path)

        print("Helmet classes:")
        print(self.model.names)

    # =====================================================
    # HEAD CROP
    # =====================================================

    def get_head_crop(self, frame, person_bbox):

        x1, y1, x2, y2 = person_bbox

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            return None, None

        # -------------------------------------------------
        # HEAD REGION
        # -------------------------------------------------

        head_y1 = y1

        head_y2 = (
            y1 +
            int(height * 0.45)
        )

        # Extra horizontal padding
        pad_x = int(width * 0.30)

        head_x1 = max(
            0,
            x1 - pad_x
        )

        head_x2 = min(
            frame.shape[1],
            x2 + pad_x
        )

        head_y1 = max(
            0,
            head_y1
        )

        head_y2 = min(
            frame.shape[0],
            head_y2
        )

        crop = frame[
            head_y1:head_y2,
            head_x1:head_x2
        ]

        if crop.size == 0:
            return None, None

        # -------------------------------------------------
        # UPSCALE
        # -------------------------------------------------

        crop = cv2.resize(
            crop,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        bbox = [
            head_x1,
            head_y1,
            head_x2,
            head_y2
        ]

        return crop, bbox

    # =====================================================
    # HELMET CLASSIFICATION
    # =====================================================

    def classify_person(
        self,
        frame,
        person_bbox
    ):

        crop, bbox = self.get_head_crop(
            frame,
            person_bbox
        )

        if crop is None:

            return {
                "class": "UNKNOWN",
                "confidence": 0.0,
                "helmet_probability": 0.0,
                "no_helmet_probability": 0.0,
                "difference": 0.0,
                "bbox": None
            }

        # =================================================
        # RUN CLASSIFIER
        # =================================================

        results = self.model(
            crop,
            imgsz=224,
            verbose=False
        )

        if not results:

            return {
                "class": "UNKNOWN",
                "confidence": 0.0,
                "helmet_probability": 0.0,
                "no_helmet_probability": 0.0,
                "difference": 0.0,
                "bbox": bbox
            }

        result = results[0]

        if result.probs is None:

            return {
                "class": "UNKNOWN",
                "confidence": 0.0,
                "helmet_probability": 0.0,
                "no_helmet_probability": 0.0,
                "difference": 0.0,
                "bbox": bbox
            }

        # =================================================
        # GET CLASS PROBABILITIES
        # =================================================

        probs = (
            result.probs.data
            .cpu()
            .numpy()
        )

        helmet_probability = 0.0
        no_helmet_probability = 0.0

        for class_id, probability in enumerate(probs):

            class_name = (
                self.model.names[class_id]
                .lower()
                .strip()
            )

            probability = float(
                probability
            )

            # ---------------------------------------------
            # HELMET
            # ---------------------------------------------

            if class_name == "helmet":

                helmet_probability = probability

            # ---------------------------------------------
            # NO HELMET
            # ---------------------------------------------

            elif class_name in [
                "no_helmet",
                "no helmet",
                "no-helmet"
            ]:

                no_helmet_probability = probability

        # =================================================
        # PROBABILITY DIFFERENCE
        # =================================================

        difference = (
            helmet_probability
            -
            no_helmet_probability
        )
        print(
    f"[HELMET DEBUG] "
    f"helmet={helmet_probability:.3f} | "
    f"no_helmet={no_helmet_probability:.3f}"
)

        # =================================================
        # HIGH SENSITIVITY DECISION
        # =================================================

        # -------------------------------------------------
        # PRIORITY 1
        # NO HELMET
        #
        # If no-helmet is at least 40% and is stronger
        # than helmet prediction, flag violation.
        # -------------------------------------------------

        if (
            no_helmet_probability >= 0.40
            and
            no_helmet_probability >= helmet_probability
        ):

            final_class = "no_helmet"

            final_confidence = (
                no_helmet_probability
            )

        # -------------------------------------------------
        # PRIORITY 2
        # HELMET
        #
        # Helmet must have a reasonable confidence and
        # must be stronger than no-helmet.
        # -------------------------------------------------

        elif (
            helmet_probability >= 0.50
            and
            helmet_probability > no_helmet_probability
        ):

            final_class = "helmet"

            final_confidence = (
                helmet_probability
            )

        # -------------------------------------------------
        # PRIORITY 3
        # UNCERTAIN
        # -------------------------------------------------

        else:

            final_class = "UNKNOWN"

            final_confidence = max(
                helmet_probability,
                no_helmet_probability
            )

        # =================================================
        # RESULT
        # =================================================

        return {

            "class": final_class,

            "confidence": round(
                final_confidence,
                3
            ),

            "helmet_probability": round(
                helmet_probability,
                3
            ),

            "no_helmet_probability": round(
                no_helmet_probability,
                3
            ),

            "difference": round(
                difference,
                3
            ),

            "bbox": bbox
        }