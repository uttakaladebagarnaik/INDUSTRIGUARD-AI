import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/industrialguard_ppe/weights/best.pt"

model = YOLO(MODEL_PATH)

print("PPE MODEL CLASSES:")
print(model.names)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera not opened")
    exit()

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Very low confidence for diagnostic testing
    results = model(
        frame,
        conf=0.01,
        verbose=False
    )

    result = results[0]

    print("\nDETECTIONS:")

    for box in result.boxes:

        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        class_name = model.names[class_id]

        x1, y1, x2, y2 = map(
            int,
            box.xyxy[0].tolist()
        )

        print(
            class_name,
            round(confidence, 3)
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
            f"{class_name} {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

    cv2.imshow(
        "PPE MODEL DIAGNOSTIC",
        frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()