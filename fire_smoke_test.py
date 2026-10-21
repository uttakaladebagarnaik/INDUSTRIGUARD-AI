from ultralytics import YOLO
import cv2

MODEL_PATH = "runs/detect/industrialguard_fire_smoke/weights/best.pt"

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("ERROR: Failed to read camera.")
        break

    results = model(
        frame,
        conf=0.20,
        device=0,
        verbose=False
    )

    annotated = results[0].plot()

    cv2.imshow("INDUSTRIGUARD AI - Fire & Smoke Detection", annotated)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()