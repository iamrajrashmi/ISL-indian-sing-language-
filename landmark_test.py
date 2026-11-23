print("ISL Landmark Detection Started!")
import cv2
import mediapipe as mp

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Hand detection
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Webcam
cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        hand_count = len(results.multi_hand_landmarks)

        for hand_landmarks in results.multi_hand_landmarks:

            # Draw landmarks
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

            # Extract coordinates
            landmarks = []

            for point in hand_landmarks.landmark:

                landmarks.extend([
                    point.x,
                    point.y,
                    point.z
                ])

            print("Total features:", len(landmarks))

            print("First 3 landmarks:", landmarks[:9])

        cv2.putText(
            frame,
            f"Hands Detected: {hand_count}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow("ISL Landmark Extraction", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
hands.close()
cv2.destroyAllWindows()