import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
import time

from collections import deque, Counter

# ==========================================
# 1. LOAD ALPHABET MODEL
# ==========================================

print("Loading ISL Alphabet Model...")

alphabet_data = joblib.load("models/isl_alphabet_model.pkl")

alphabet_model = alphabet_data["model"]
alphabet_columns = alphabet_data["feature_columns"]

alphabet_model.n_jobs = 1

print("Alphabet model loaded!")

# ==========================================
# 2. LOAD GREETING MODEL
# ==========================================

print("\nLoading Greeting Model...")

greeting_data = joblib.load("models/greeting_model.pkl")

greeting_model = greeting_data["model"]

print("Greeting model loaded!")

print("\nGestures:", greeting_model.classes_)

# ==========================================
# 3. MEDIAPIPE SETUP
# ==========================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ==========================================
# 4. EXTRACT HAND LANDMARKS
# ==========================================

def extract_landmarks(results):

    left_hand = [0.0] * 63
    right_hand = [0.0] * 63

    if results.multi_hand_landmarks:

        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):

            hand_label = handedness.classification[0].label

            values = []

            for landmark in hand_landmarks.landmark:
                values.extend([
                    landmark.x,
                    landmark.y,
                    landmark.z
                ])

            if hand_label == "Left":
                left_hand = values
            else:
                right_hand = values

    return left_hand + right_hand


# ==========================================
# 5. VARIABLES
# ==========================================

mode = None

alphabet_predictions = deque(maxlen=10)

greeting_sequence = []

last_capture_time = 0

last_greeting = "Waiting..."

last_confidence = 0

sequence_length = 30

# ==========================================
# 6. OPEN WEBCAM
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened!")
    exit()

print("\n================================")
print("       COMBINED ISL APP")
print("================================")
print("Press 1 = Alphabet Recognition")
print("Press 2 = Greeting Recognition")
print("Press Q = Quit")
print("================================")

# ==========================================
# 7. MAIN LOOP
# ==========================================

while True:

    success, frame = cap.read()

    if not success:
        print("Camera frame not received.")
        break

    frame = cv2.flip(frame, 1)

    rgb_frame = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb_frame)

    landmarks = extract_landmarks(results)

    # Draw hand landmarks

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # ======================================
    # ALPHABET MODE
    # ======================================

    if mode == "alphabet":

        if np.any(landmarks):

            alphabet_df = pd.DataFrame(
                [landmarks],
                columns=alphabet_columns
            )

            probabilities = alphabet_model.predict_proba(
                alphabet_df
            )[0]

            prediction = alphabet_model.classes_[
                np.argmax(probabilities)
            ]

            confidence = np.max(probabilities)

            if confidence >= 0.50:
                alphabet_predictions.append(prediction)

        if alphabet_predictions:

            final_prediction = Counter(
                alphabet_predictions
            ).most_common(1)[0][0]

            cv2.putText(
                frame,
                "Alphabet: " + str(final_prediction),
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "Show a hand sign",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

    # ======================================
    # GREETING MODE
    # ======================================

    elif mode == "greeting":

        current_time = time.time()

        if current_time - last_capture_time >= 0.2:

            greeting_sequence.append(landmarks)

            last_capture_time = current_time

        cv2.putText(
            frame,
            "Recording: " + str(len(greeting_sequence)) + "/30",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        if len(greeting_sequence) >= sequence_length:

            input_data = np.array(
                greeting_sequence[:sequence_length]
            ).flatten().reshape(1, -1)

            probabilities = greeting_model.predict_proba(
                input_data
            )[0]

            best_index = np.argmax(probabilities)

            last_greeting = greeting_model.classes_[best_index]

            last_confidence = probabilities[best_index] * 100

            print(
                "Detected:",
                last_greeting,
                "| Confidence:",
                round(last_confidence, 2),
                "%"
            )

            greeting_sequence = []

        cv2.putText(
            frame,
            "Greeting: " + str(last_greeting),
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Confidence: " + str(round(last_confidence, 1)) + "%",
            (20, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

    # ======================================
    # DISPLAY CURRENT MODE
    # ======================================

    if mode == "alphabet":
        mode_text = "MODE: ALPHABET"

    elif mode == "greeting":
        mode_text = "MODE: GREETING"

    else:
        mode_text = "MODE: SELECT (Press 1 or 2)"

    cv2.putText(
        frame,
        mode_text,
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.imshow("Combined ISL Recognition", frame)

    # ======================================
    # KEYBOARD CONTROLS
    # ======================================

    key = cv2.waitKey(1) & 0xFF

    if key == ord("1"):

        mode = "alphabet"

        alphabet_predictions.clear()
        greeting_sequence = []

        print("Alphabet mode activated.")

    elif key == ord("2"):

        mode = "greeting"

        greeting_sequence = []
        last_capture_time = time.time()

        last_greeting = "Waiting..."
        last_confidence = 0

        print("Greeting mode activated.")

    elif key == ord("q") or key == ord("Q"):

        print("Recognition stopped.")
        break


# ==========================================
# 8. CLEANUP
# ==========================================

cap.release()

hands.close()

cv2.destroyAllWindows()