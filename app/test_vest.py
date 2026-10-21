import cv2
from ultralytics import YOLO

# =========================
# MODEL
# =========================

MODEL_PATH = "runs/detect/industrialguard_ppe_v2-2/weights/best.pt"

model = YOLO(MODEL_PATH)

print("PPE model loaded!")
print("Classes:", model.names)

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

    # Run PPE detection
    results = model(
        frame,
        conf=0.10,
        imgsz=960,
        iou=0.45,
        max_det=50,
        verbose=False
    )

    result = results[0]

    vest_found = False

    if result.boxes is not None:

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = model.names[class_id]

            if class_name != "safety_vest":
                continue

            vest_found = True

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            # Draw vest box
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                3
            )

            label = (
                f"SAFETY VEST "
                f"{confidence * 100:.1f}%"
            )

            cv2.putText(
                frame,
                label,
                (x1, max(30, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

    # =========================
    # STATUS
    # =========================

    if vest_found:

        status = "VEST DETECTED"
        status_color = (0, 255, 0)

    else:

        status = "VEST NOT DETECTED"
        status_color = (0, 165, 255)

    # Status panel
    cv2.rectangle(
        frame,
        (10, 10),
        (430, 75),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        status,
        (25, 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        status_color,
        2
    )

    cv2.imshow(
        "INDUSTRIGUARD AI - Vest Test",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()