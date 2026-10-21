import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/industrialguard_ppe_v2/weights/best.pt"

print("Loading V2 PPE model...")
model = YOLO(MODEL_PATH)

print("MODEL:", model.names)
print("Starting camera...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not open.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    results = model(
        frame,
        conf=0.25,
        imgsz=640,
        verbose=False
    )

    result = results[0]

    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        class_name = model.names[cls_id]

        print(
            f"{class_name}: {conf:.2f}"
        )

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"{class_name} {conf:.2f}",
            (x1, max(y1 - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

    cv2.imshow(
        "INDUSTRIGUARD AI - PPE V2 TEST",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
