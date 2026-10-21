import cv2
from ultralytics import YOLO

# =========================
# MODELS
# =========================

PERSON_MODEL_PATH = "yolo11n.pt"

HELMET_MODEL_PATH = (
    "runs/classify/runs/classify/"
    "industrialguard_helmet/weights/best.pt"
)

# =========================
# SETTINGS
# =========================

PERSON_CONF = 0.20

# Helmet classifier sensitivity
HELMET_CONF = 0.55

# Minimum head crop size
MIN_HEAD_SIZE = 30

# =========================
# LOAD MODELS
# =========================

print("Loading person detector...")

person_model = YOLO(PERSON_MODEL_PATH)

print("Loading helmet classifier...")

helmet_model = YOLO(HELMET_MODEL_PATH)

print("Helmet classes:", helmet_model.names)

print("Models loaded successfully!")

# =========================
# CAMERA
# =========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

# =========================
# LOOP
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    display = frame.copy()

    # --------------------------------
    # PERSON DETECTION
    # --------------------------------

    results = person_model(
        frame,
        conf=PERSON_CONF,
        imgsz=960,
        verbose=False
    )

    persons = []

    if results and results[0].boxes is not None:

        for box in results[0].boxes:

            class_id = int(box.cls[0])

            # COCO person
            if class_id != 0:
                continue

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            width = x2 - x1
            height = y2 - y1

            if width <= 0 or height <= 0:
                continue

            persons.append(
                (x1, y1, x2, y2, confidence)
            )

    # --------------------------------
    # PROCESS PERSONS
    # --------------------------------

    for person_index, (
        x1,
        y1,
        x2,
        y2,
        person_conf
    ) in enumerate(persons):

        width = x2 - x1
        height = y2 - y1

        # --------------------------------
        # HEAD REGION
        # --------------------------------

        # More generous head region
        head_x1 = max(
            0,
            x1 - int(width * 0.18)
        )

        head_x2 = min(
            frame.shape[1],
            x2 + int(width * 0.18)
        )

        head_y1 = max(
            0,
            y1 - int(height * 0.05)
        )

        head_y2 = min(
            frame.shape[0],
            y1 + int(height * 0.42)
        )

        head_crop = frame[
            head_y1:head_y2,
            head_x1:head_x2
        ]

        if head_crop.size == 0:
            continue

        crop_h, crop_w = head_crop.shape[:2]

        if crop_w < MIN_HEAD_SIZE or crop_h < MIN_HEAD_SIZE:
            cv2.rectangle(
                display,
                (x1, y1),
                (x2, y2),
                (0, 165, 255),
                2
            )

            cv2.putText(
                display,
                "TOO FAR",
                (x1, max(25, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 165, 255),
                2
            )

            continue

        # --------------------------------
        # UPSCALE SMALL HEAD
        # --------------------------------

        scale = 3

        enlarged = cv2.resize(
            head_crop,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

        # --------------------------------
        # HELMET CLASSIFIER
        # --------------------------------

        helmet_results = helmet_model(
            enlarged,
            imgsz=224,
            verbose=False
        )

        result = helmet_results[0]

        if result.probs is None:
            continue

        class_id = int(result.probs.top1)

        confidence = float(
            result.probs.top1conf
        )

        class_name = helmet_model.names[class_id]

        # --------------------------------
        # SENSITIVITY LOGIC
        # --------------------------------

        if class_name == "helmet":

            if confidence >= HELMET_CONF:
                status = "HELMET"
                status_color = (0, 255, 0)

            else:
                status = "CHECKING"
                status_color = (0, 165, 255)

        else:

            if confidence >= HELMET_CONF:
                status = "NO HELMET"
                status_color = (0, 0, 255)

            else:
                status = "CHECKING"
                status_color = (0, 165, 255)

        # --------------------------------
        # DRAW PERSON BOX
        # --------------------------------

        cv2.rectangle(
            display,
            (x1, y1),
            (x2, y2),
            status_color,
            2
        )

        # --------------------------------
        # DRAW HEAD BOX
        # --------------------------------

        cv2.rectangle(
            display,
            (head_x1, head_y1),
            (head_x2, head_y2),
            (255, 255, 0),
            2
        )

        # --------------------------------
        # LABEL
        # --------------------------------

        label = (
            f"{status} "
            f"{confidence * 100:.1f}%"
        )

        cv2.putText(
            display,
            label,
            (x1, max(25, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            status_color,
            2
        )

    # --------------------------------
    # TOP INFORMATION
    # --------------------------------

    cv2.rectangle(
        display,
        (10, 10),
        (390, 70),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        display,
        "INDUSTRIGUARD AI",
        (25, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        display,
        f"Workers: {len(persons)}",
        (25, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    # --------------------------------
    # SHOW
    # --------------------------------

    cv2.imshow(
        "Helmet Sensitivity Test",
        display
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()