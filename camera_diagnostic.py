import cv2
import time

tests = [
    ("Camera 0 - AUTO", 0, cv2.CAP_ANY),
    ("Camera 0 - DSHOW", 0, cv2.CAP_DSHOW),
    ("Camera 0 - MSMF", 0, cv2.CAP_MSMF),

    ("Camera 1 - AUTO", 1, cv2.CAP_ANY),
    ("Camera 1 - DSHOW", 1, cv2.CAP_DSHOW),
    ("Camera 1 - MSMF", 1, cv2.CAP_MSMF),

    ("Camera 2 - AUTO", 2, cv2.CAP_ANY),
    ("Camera 2 - DSHOW", 2, cv2.CAP_DSHOW),
]

for name, index, backend in tests:

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    cap = cv2.VideoCapture(index, backend)

    if not cap.isOpened():
        print("❌ Could not open")
        cap.release()
        continue

    print("✅ Opened")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    time.sleep(1)

    success_count = 0

    for i in range(10):
        ret, frame = cap.read()

        if ret and frame is not None:
            success_count += 1

            mean_value = frame.mean()
            minimum = frame.min()
            maximum = frame.max()

            print(
                f"Frame {i+1}: "
                f"mean={mean_value:.2f}, "
                f"min={minimum}, "
                f"max={maximum}"
            )

        else:
            print(f"Frame {i+1}: ❌ FAILED")

        time.sleep(0.1)

    print(f"Successful frames: {success_count}/10")

    if success_count > 0:
        ret, frame = cap.read()

        if ret:
            cv2.imshow(name, frame)

            print("👉 Press any key to close this test window.")
            cv2.waitKey(2000)

    cap.release()
    cv2.destroyAllWindows()

print("\n")
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)