import cv2

print("Testing camera...")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("❌ Camera open nahi hua")
    exit()

print("✅ Camera opened")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Frame read failed")
        break

    print("Frame:", frame.shape)

    cv2.imshow("Camera Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()