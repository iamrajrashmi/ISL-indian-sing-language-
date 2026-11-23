import cv2
import mediapipe as mp

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize hand detection
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Start webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot access webcam!")
    exit()

print("Hand detection started!")
print("Show one or both hands.")
print("Press Q to exit.")

while True:

    success, frame = cap.read()

    if not success:
        print("Cannot read webcam!")
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb_frame)

    hand_count = 0

    if results.multi_hand_landmarks:

        hand_count = len(results.multi_hand_landmarks)

        for hand_landmarks in results.multi_hand_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # Display hand count
    cv2.putText(
        frame,
        f"Hands Detected: {hand_count}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("ISL Hand Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()

print("Hand detection closed!")