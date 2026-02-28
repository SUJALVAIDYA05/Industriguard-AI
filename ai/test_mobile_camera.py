import cv2

# Replace with YOUR phone's IP address
MOBILE_URL = "http://192.168.0.101:8080/video"

print(f"Connecting to: {MOBILE_URL}")
print("Press Q to quit\n")

cap = cv2.VideoCapture(MOBILE_URL)

if not cap.isOpened():
    print("❌ Could not connect to mobile camera")
    print("   Check:")
    print("   1. IP Webcam app is running on phone")
    print("   2. Phone and laptop on same WiFi")
    print("   3. IP address is correct")
else:
    print("✅ Connected to mobile camera!")

while True:
    ret, frame = cap.read()

    if not ret:
        print("⚠ Frame dropped — reconnecting...")
        cap = cv2.VideoCapture(MOBILE_URL)
        continue

    cv2.putText(
        frame,
        f"Mobile Camera — IndustriGuard AI",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8, (0, 255, 255), 2
    )

    cv2.imshow("Mobile Camera Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Test complete")