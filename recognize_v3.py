import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
import os
import time

from collections import deque, Counter

# ==========================================
# 1. LOAD MODEL
# ==========================================

MODEL_PATH = "models/isl_alphabet_model_v3.pkl"

print("Loading ISL Alphabet V3 Model...")

if not os.path.exists(MODEL_PATH):
    print("ERROR: Model not found!")
    raise SystemExit

model = joblib.load(MODEL_PATH)

# Avoid multiprocessing issues
model.n_jobs = 1

print("Model loaded successfully!")
print("Alphabets:", model.classes_)

# ==========================================
# 2. MEDIAPIPE SETUP
# ==========================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ==========================================
# 3. SETTINGS
# ==========================================

SMOOTHING_SIZE = 10
REQUIRED_COUNT = 6
CONFIDENCE_THRESHOLD = 0.55

prediction_history = deque(maxlen=SMOOTHING_SIZE)

word = ""

last_key_time = 0
KEY_DELAY = 0.4

# ==========================================
# 4. FEATURE EXTRACTION
# ==========================================

def extract_features(results):

    left_hand = [0.0] * 63
    right_hand = [0.0] * 63

    if results.multi_hand_landmarks:

        for i, hand_landmarks in enumerate(
            results.multi_hand_landmarks
        ):

            handedness = (
                results.multi_handedness[i]
                .classification[0].label
            )

            values = []

            for landmark in hand_landmarks.landmark:

                values.extend([
                    landmark.x,
                    landmark.y,
                    landmark.z
                ])

            if handedness == "Left":
                left_hand = values
            else:
                right_hand = values

    return left_hand + right_hand

# ==========================================
# 5. START WEBCAM
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened!")
    hands.close()
    raise SystemExit

print("\nISL Alphabet Recognition Started!")
print("----------------------------------")
print("SPACE    = Add recognized letter")
print("BACKSPACE = Delete last letter")
print("ENTER    = Clear word")
print("S        = Save word")
print("Q        = Quit")
print("----------------------------------")

# ==========================================
# 6. MAIN RECOGNITION LOOP
# ==========================================

while True:

    success, frame = cap.read()

    if not success:
        print("Unable to read webcam frame.")
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb)

    hand_count = 0
    current_prediction = "NO HAND"
    confidence = 0.0
    stable_prediction = "WAITING"

    # ======================================
    # DETECT HANDS
    # ======================================

    if results.multi_hand_landmarks:

        hand_count = len(results.multi_hand_landmarks)

        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

        # ==================================
        # EXTRACT FEATURES
        # ==================================

        features = extract_features(results)

        feature_names = model.feature_names_in_

        input_data = pd.DataFrame(
            [features],
            columns=feature_names
        )

        # ==================================
        # PREDICT ALPHABET
        # ==================================

        probabilities = model.predict_proba(input_data)[0]

        best_index = np.argmax(probabilities)

        current_prediction = model.classes_[best_index]

        confidence = probabilities[best_index]

        prediction_history.append(
            (current_prediction, confidence)
        )

        # ==================================
        # STABILIZE PREDICTION
        # ==================================

        labels = [
            item[0] for item in prediction_history
        ]

        counts = Counter(labels)

        most_common = counts.most_common(1)[0]

        if most_common[1] >= REQUIRED_COUNT:

            selected_label = most_common[0]

            selected_confidences = [
                conf
                for label, conf in prediction_history
                if label == selected_label
            ]

            average_confidence = np.mean(
                selected_confidences
            )

            if average_confidence >= CONFIDENCE_THRESHOLD:

                stable_prediction = selected_label

                confidence = average_confidence

            else:
                stable_prediction = "UNCERTAIN"

        else:
            stable_prediction = "STABILIZING"

    else:

        prediction_history.clear()

    # ======================================
    # DISPLAY INFORMATION
    # ======================================

    cv2.rectangle(
        frame,
        (10, 10),
        (640, 210),
        (30, 30, 30),
        -1
    )

    cv2.putText(
        frame,
        "ISL ALPHABET RECOGNIZER V3",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Prediction: " + stable_prediction,
        (20, 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Current: " + current_prediction,
        (20, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Confidence: " + str(round(confidence * 100, 1)) + "%",
        (20, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Hands detected: " + str(hand_count),
        (20, 190),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # ======================================
    # DISPLAY WORD
    # ======================================

    cv2.rectangle(
        frame,
        (10, 230),
        (640, 300),
        (50, 50, 50),
        -1
    )

    cv2.putText(
        frame,
        "WORD: " + word,
        (20, 275),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "SPACE:Add  BACKSPACE:Delete  ENTER:Clear  S:Save  Q:Quit",
        (10, 340),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (255, 255, 255),
        1
    )

    cv2.imshow(
        "ISL Alphabet Recognition V3",
        frame
    )

    # ======================================
    # KEYBOARD CONTROLS
    # ======================================

    key = cv2.waitKey(1) & 0xFF

    current_time = time.time()

    if key == ord("q"):
        break

    if current_time - last_key_time >= KEY_DELAY:

        # ADD LETTER
        if key == 32:

            if stable_prediction in model.classes_:

                word += stable_prediction

                print("Added:", stable_prediction)
                print("Current word:", word)

                last_key_time = current_time

        # DELETE LETTER
        elif key == 8:

            word = word[:-1]

            print("Current word:", word)

            last_key_time = current_time

        # CLEAR WORD
        elif key == 13:

            word = ""

            print("Word cleared!")

            last_key_time = current_time

        # SAVE WORD
        elif key == ord("s"):

            if word:

                with open(
                    "recognized_words.txt",
                    "a",
                    encoding="utf-8"
                ) as file:

                    file.write(word + "\n")

                print("Word saved:", word)

            last_key_time = current_time

# ==========================================
# 7. CLOSE PROGRAM
# ==========================================

cap.release()
cv2.destroyAllWindows()
hands.close()

print("\nISL recognition stopped.")
print("Final word:", word)