import cv2
import os
from ultralytics import YOLO

# =========================
# SETTINGS
# =========================

MODEL_PATH = "yolo11n.pt"

HELMET_DIR = "helmet_dataset/raw/helmet"
NO_HELMET_DIR = "helmet_dataset/raw/no_helmet"

os.makedirs(HELMET_DIR, exist_ok=True)
os.makedirs(NO_HELMET_DIR, exist_ok=True)

# =========================
# LOAD PERSON MODEL
# =========================

print("Loading YOLO person detector...")

model = YOLO(MODEL_PATH)

print("Model loaded!")
print("Press:")
print(" H = Helmet ON")
print(" N = No Helmet")
print(" Q = Quit")

# =========================
# CAMERA
# =========================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

helmet_count = len(os.listdir(HELMET_DIR))
no_helmet_count = len(os.listdir(NO_HELMET_DIR))

print(f"Existing Helmet images: {helmet_count}")
print(f"Existing No Helmet images: {no_helmet_count}")

# =========================
# MAIN LOOP
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        print("Camera frame failed.")
        break

    # Detect persons
    results = model(
        frame,
        conf=0.35,
        imgsz=640,
        verbose=False
    )

    persons = []

    if results and results[0].boxes is not None:

        for box in results[0].boxes:

            class_id = int(box.cls[0])

            # COCO class 0 = person
            if class_id != 0:
                continue

            confidence = float(box.conf[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            area = max(0, x2 - x1) * max(0, y2 - y1)

            persons.append(
                (area, x1, y1, x2, y2)
            )

    # =========================
    # SELECT LARGEST PERSON
    # =========================

    if persons:

        persons.sort(reverse=True)

        _, x1, y1, x2, y2 = persons[0]

        width = x2 - x1
        height = y2 - y1

        # Head + helmet region
        crop_y1 = y1
        crop_y2 = y1 + int(height * 0.45)

        # Add a little horizontal padding
        pad_x = int(width * 0.15)

        crop_x1 = max(0, x1 - pad_x)
        crop_x2 = min(frame.shape[1], x2 + pad_x)

        head_crop = frame[
            crop_y1:crop_y2,
            crop_x1:crop_x2
        ]

        # Draw person/head region
        cv2.rectangle(
            frame,
            (crop_x1, crop_y1),
            (crop_x2, crop_y2),
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "HEAD / HELMET REGION",
            (crop_x1, max(25, crop_y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

        # =========================
        # KEYBOARD INPUT
        # =========================

        key = cv2.waitKey(1) & 0xFF

        # Helmet ON
        if key == ord("h"):

            if head_crop.size > 0:

                filename = (
                    f"helmet_{helmet_count:04d}.jpg"
                )

                path = os.path.join(
                    HELMET_DIR,
                    filename
                )

                cv2.imwrite(path, head_crop)

                helmet_count += 1

                print(
                    f"[HELMET] Saved: {filename}"
                )

        # No Helmet
        elif key == ord("n"):

            if head_crop.size > 0:

                filename = (
                    f"no_helmet_{no_helmet_count:04d}.jpg"
                )

                path = os.path.join(
                    NO_HELMET_DIR,
                    filename
                )

                cv2.imwrite(path, head_crop)

                no_helmet_count += 1

                print(
                    f"[NO HELMET] Saved: {filename}"
                )

        # Quit
        elif key == ord("q"):
            break

        # =========================
        # UI
        # =========================

        cv2.rectangle(
            frame,
            (10, 10),
            (500, 105),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            frame,
            "H = HELMET ON",
            (25, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "N = NO HELMET",
            (25, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 165, 255),
            2
        )

        cv2.putText(
            frame,
            "Q = QUIT",
            (25, 96),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Helmet: {helmet_count}",
            (frame.shape[1] - 260, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"No Helmet: {no_helmet_count}",
            (frame.shape[1] - 260, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 165, 255),
            2
        )

    else:

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        cv2.putText(
            frame,
            "No person detected",
            (25, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "INDUSTRIGUARD AI - Helmet Dataset Collector",
        frame
    )

# =========================
# CLEANUP
# =========================

cap.release()
cv2.destroyAllWindows()

print("\nDataset collection finished!")
print(f"Helmet images: {helmet_count}")
print(f"No Helmet images: {no_helmet_count}")