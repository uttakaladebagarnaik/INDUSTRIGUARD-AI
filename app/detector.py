from ultralytics import YOLO
import cv2


# Load YOLO model
model = YOLO("yolo11n.pt")


# Open laptop webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()


print("INDUSTRIGUARD AI - Camera Started")
print("Press Q to quit.")


while True:
    ret, frame = cap.read()

    if not ret:
        print("ERROR: Could not read camera frame.")
        break

    # Run YOLO detection
    results = model(frame, verbose=False)

    # Draw detections
    annotated_frame = results[0].plot()

    # Display
    cv2.imshow("INDUSTRIGUARD AI - Live Detection", annotated_frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()