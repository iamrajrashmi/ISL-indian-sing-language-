import cv2
import mediapipe as mp
import numpy as np
import joblib

from collections import deque, Counter
from datetime import datetime

# ==========================================
# 1. LOAD TRAINED A-Z MODEL
# ==========================================

print("Loading improved ISL alphabet model...")

MODEL_PATH = "models/isl_alphabet_model_v2.pkl"

model = joblib.load(MODEL_PATH)

FEATURE_NAMES = list(model.feature_names_in_)

if len(FEATURE_NAMES) != 126:
    raise ValueError("Model must contain exactly 126 features!")

print("Model loaded successfully!")
print("Available alphabets:", model.classes_)

# ==========================================
# 2. MEDIAPIPE SETUP
# ==========================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

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

CONFIDENCE_THRESHOLD = 60
SMOOTHING_FRAMES = 10
STABILITY_REQUIRED = 6

prediction_history = deque(maxlen=SMOOTHING_FRAMES)

word = ""

# ==========================================
# 4. OPEN WEBCAM
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open webcam!")
    raise SystemExit

print("\nISL ALPHABET RECOGNITION")
print("--------------------------------")
print("SPACE     = Add detected letter")
print("BACKSPACE = Delete last letter")
print("ENTER     = Clear word")
print("S         = Save word")
print("Q         = Exit")
print("--------------------------------")

# ==========================================
# 5. MAIN LOOP
# ==========================================

try:

    while True:

        success, frame = cap.read()

        if not success:
            print("Cannot read webcam!")
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(rgb)

        left_hand = [0.0] * 63
        right_hand = [0.0] * 63

        detected_hands = 0

        # ==================================
        # 6. EXTRACT HAND LANDMARKS
        # ==================================

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

        # ==================================
        # 7. PREDICT ALPHABET
        # ==================================

        current_letter = "NO HAND"
        confidence = 0

        if detected_hands > 0:

            features = left_hand + right_hand

            input_data = np.array(
                features,
                dtype=np.float64
            ).reshape(1, -1)

            import pandas as pd

            input_df = pd.DataFrame(
                input_data,
                columns=FEATURE_NAMES
            )

            probabilities = model.predict_proba(input_df)[0]

            best_index = np.argmax(probabilities)

            confidence = probabilities[best_index] * 100

            predicted_letter = model.classes_[best_index]

            if confidence >= CONFIDENCE_THRESHOLD:

                prediction_history.append(predicted_letter)

                counts = Counter(prediction_history)

                stable_letter, stable_count = counts.most_common(1)[0]

                if stable_count >= STABILITY_REQUIRED:

                    current_letter = stable_letter

                else:
                    current_letter = "WAIT..."

            else:

                prediction_history.clear()

                current_letter = "UNCERTAIN"

        else:

            prediction_history.clear()

        # ==================================
        # 8. DISPLAY CURRENT LETTER
        # ==================================

        cv2.putText(
            frame,
            "ISL ALPHABET RECOGNITION",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Detected: {current_letter}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 255),
            3
        )

        cv2.putText(
            frame,
            f"Confidence: {confidence:.1f}%",
            (20, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Hands: {detected_hands}",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # ==================================
        # 9. WORD BUILDER
        # ==================================

        cv2.rectangle(
            frame,
            (10, 200),
            (630, 290),
            (50, 50, 50),
            -1
        )

        cv2.putText(
            frame,
            "YOUR WORD:",
            (25, 230),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        display_word = word[-25:]

        cv2.putText(
            frame,
            display_word,
            (25, 275),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (0, 255, 0),
            2
        )

        # ==================================
        # 10. KEY INSTRUCTIONS
        # ==================================

        cv2.putText(
            frame,
            "SPACE: ADD LETTER",
            (20, 340),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "BACKSPACE: DELETE",
            (20, 375),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "ENTER: CLEAR WORD",
            (20, 410),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "S: SAVE WORD | Q: EXIT",
            (20, 445),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "ISL Alphabet Recognition V2",
            frame
        )

        # ==================================
        # 11. KEYBOARD CONTROLS
        # ==================================

        key = cv2.waitKey(1) & 0xFF

        # Add stable letter
        if key == 32:

            if current_letter in model.classes_:

                word += current_letter

                print(
                    "Letter added:",
                    current_letter,
                    "| Word:",
                    word
                )

            else:

                print("No stable letter detected!")

        # Backspace
        elif key == 8:

            word = word[:-1]

            print("Current word:", word)

        # Enter clears word
        elif key == 13:

            word = ""

            print("Word cleared!")

        # Save word
        elif key == ord("s"):

            if word:

                with open(
                    "recognized_words.txt",
                    "a",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        f"{datetime.now()} : {word}\n"
                    )

                print("Word saved:", word)

            else:

                print("No word to save!")

        # Exit
        elif key == ord("q"):

            print("Closing recognition...")
            break

finally:

    cap.release()

    hands.close()

    cv2.destroyAllWindows()

    print("\nISL recognition stopped.")