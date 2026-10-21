import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/industrialguard_ppe_v2/weights/best.pt"

print("Loading PPE model...")
model = YOLO(MODEL_PATH)

print("\nPPE CLASSES:")
print(model.names)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera not found.")
    exit()

print("\nCamera started.")
print("Press Q to quit.")

while True:

    ret, frame = cap.read()

    if not ret:
        print("ERROR: Failed to read frame.")
        break

    results = model(
        frame,
        conf=0.10,
        imgsz=960,
        iou=0.45,
        max_det=50,
        verbose=False
    )

    result = results[0]

    if result.boxes is not None:

        for box in result.boxes:

            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = model.names[class_id]

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            print(
                f"DETECTED: {class_name} | "
                f"Confidence: {confidence:.2f}"
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"{class_name} {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    cv2.imshow(
        "INDUSTRIGUARD AI - PPE RAW TEST",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()