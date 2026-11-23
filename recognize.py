import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd

from collections import deque, Counter

# =====================================
# 1. LOAD TRAINED MODEL
# =====================================

print("Loading ISL model...")

model_data = joblib.load("models/isl_alphabet_model.pkl")

model = model_data["model"]
model.n_jobs = 1

feature_columns = model_data["feature_columns"]

print("Model loaded successfully!")

# =====================================
# 2. MEDIAPIPE SETUP
# =====================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

prediction_history = deque(maxlen=10)

# =====================================
# 3. START WEBCAM
# =====================================

with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
) as hands:

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Cannot open webcam!")
        raise SystemExit

    print("Webcam started!")
    print("Press Q to exit.")

    # =====================================
    # 4. MAIN LOOP
    # =====================================

    while True:

        success, frame = cap.read()

        if not success:
            print("Cannot read webcam!")
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = hands.process(rgb)

        left_hand = [0.0] * 63
        right_hand = [0.0] * 63

        detected_hands = 0

        # =====================================
        # 5. EXTRACT HAND LANDMARKS
        # =====================================

        if results.multi_hand_landmarks:

            detected_hands = len(
                results.multi_hand_landmarks
            )

            for i, hand_landmarks in enumerate(
                results.multi_hand_landmarks
            ):

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                side = "Right"

                if results.multi_handedness:

                    side = (
                        results.multi_handedness[i]
                        .classification[0].label
                    )

                hand_data = []

                for point in hand_landmarks.landmark:

                    hand_data.extend([
                        point.x,
                        point.y,
                        point.z
                    ])

                if side == "Left":
                    left_hand = hand_data
                else:
                    right_hand = hand_data

        # =====================================
        # 6. PREDICT ALPHABET
        # =====================================

        if detected_hands > 0:

            features = left_hand + right_hand

            input_data = np.array(
                [features],
                dtype=float
            )

            input_df = pd.DataFrame(
                input_data,
                columns=feature_columns
            )

            probabilities = model.predict_proba(
                input_df
            )[0]

            best_index = np.argmax(probabilities)

            predicted_letter = model.classes_[best_index]

            confidence = probabilities[best_index] * 100

            prediction_history.append(predicted_letter)

            final_prediction = Counter(
                prediction_history
            ).most_common(1)[0][0]

            # =====================================
            # 7. DISPLAY PREDICTION
            # =====================================

            cv2.putText(
                frame,
                f"Prediction: {final_prediction}",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                3
            )

            cv2.putText(
                frame,
                f"Confidence: {confidence:.1f}%",
                (10, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Hands: {detected_hands}",
                (10, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

        else:

            prediction_history.clear()

            cv2.putText(
                frame,
                "Show your hand sign",
                (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

        # =====================================
        # 8. DISPLAY WEBCAM
        # =====================================

        cv2.putText(
            frame,
            "Q = EXIT",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "ISL Alphabet Recognition",
            frame
        )

        # =====================================
        # 9. KEYBOARD INPUT
        # =====================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

    # =====================================
    # 10. RELEASE WEBCAM
    # =====================================

    cap.release()
    cv2.destroyAllWindows()

print("Recognition program closed!")