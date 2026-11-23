import cv2
import mediapipe as mp
import joblib
import numpy as np
import pandas as pd
import os
import time
import threading
import queue
import pythoncom
import win32com.client

from collections import deque, Counter

# ==========================================
# 1. LOAD V4 MODEL
# ==========================================

MODEL_PATH = "models/isl_alphabet_model_v4.pkl"

print("Loading ISL Alphabet V4 Model...")

if not os.path.exists(MODEL_PATH):
    print("ERROR: V4 model not found!")
    raise SystemExit

model = joblib.load(MODEL_PATH)
model.n_jobs = 1

print("Model loaded successfully!")
print("Alphabets:", model.classes_)

# ==========================================
# 2. WINDOWS VOICE OUTPUT
# ==========================================

speech_queue = queue.Queue()

def speech_worker():

    pythoncom.CoInitialize()

    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100

        while True:

            text = speech_queue.get()

            if text is None:
                speech_queue.task_done()
                break

            try:
                print("Speaking:", text)

                # Synchronous speech: finish this item
                # before moving to the next one.
                speaker.Speak(str(text))

            except Exception as error:
                print("Voice error:", error)

            finally:
                speech_queue.task_done()

    finally:
        pythoncom.CoUninitialize()


speech_thread = threading.Thread(
    target=speech_worker,
    daemon=True
)

speech_thread.start()


def speak(text):
    speech_queue.put(str(text))


print("Alphabet voice output enabled!")

# ==========================================
# 3. MEDIAPIPE
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
# 4. SETTINGS
# ==========================================

SMOOTHING_SIZE = 15
REQUIRED_COUNT = 10
CONFIDENCE_THRESHOLD = 0.65

prediction_history = deque(maxlen=SMOOTHING_SIZE)

word = ""

last_key_time = 0
KEY_DELAY = 0.6

stable_prediction = "WAITING"
current_prediction = "WAITING"
confidence = 0.0

last_spoken_prediction = None

# ==========================================
# 5. NORMALIZE ONE HAND
# ==========================================

def normalize_hand(values):

    values = np.array(values, dtype=float)

    if np.all(values == 0):
        return [0.0] * 63

    points = values.reshape(21, 3)

    points = points - points[0]

    distances = np.linalg.norm(points, axis=1)

    scale = np.max(distances)

    if scale > 0:
        points = points / scale

    return points.flatten().tolist()

# ==========================================
# 6. EXTRACT FEATURES
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

    left_hand = normalize_hand(left_hand)
    right_hand = normalize_hand(right_hand)

    return left_hand + right_hand

# ==========================================
# 7. START WEBCAM
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened!")
    hands.close()
    speech_queue.put(None)
    speech_queue.join()
    speech_thread.join()
    raise SystemExit

print("\n==================================")
print("ISL ALPHABET RECOGNITION V4")
print("==================================")
print("Voice output enabled!")
print("SPACE     = Add stable letter")
print("BACKSPACE = Delete last letter")
print("ENTER     = Clear word")
print("S         = Save and speak word")
print("Q         = Quit")
print("==================================")

# ==========================================
# 8. MAIN LOOP
# ==========================================

try:

    while True:

        success, frame = cap.read()

        if not success:
            print("Unable to read webcam.")
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

        # ==================================
        # HAND DETECTION
        # ==================================

        if results.multi_hand_landmarks:

            hand_count = len(results.multi_hand_landmarks)

            for hand_landmarks in results.multi_hand_landmarks:

                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

            # FEATURE EXTRACTION

            features = extract_features(results)

            input_data = pd.DataFrame(
                [features],
                columns=model.feature_names_in_
            )

            # PREDICTION

            probabilities = model.predict_proba(input_data)[0]

            best_index = np.argmax(probabilities)

            current_prediction = model.classes_[best_index]

            confidence = float(probabilities[best_index])

            prediction_history.append(
                (current_prediction, confidence)
            )

            # STABILIZATION

            labels = [
                item[0] for item in prediction_history
            ]

            counts = Counter(labels)

            selected_label, selected_count = counts.most_common(1)[0]

            if selected_count >= REQUIRED_COUNT:

                selected_confidences = [
                    conf for label, conf in prediction_history
                    if label == selected_label
                ]

                average_confidence = float(
                    np.mean(selected_confidences)
                )

                if average_confidence >= CONFIDENCE_THRESHOLD:

                    stable_prediction = selected_label
                    confidence = average_confidence

                else:
                    stable_prediction = "UNCERTAIN"

            else:
                stable_prediction = "STABILIZING"

            # SPEAK EACH NEW STABLE LETTER

            if stable_prediction in model.classes_:

                if stable_prediction != last_spoken_prediction:

                    speak(stable_prediction)

                    last_spoken_prediction = stable_prediction

        else:

            prediction_history.clear()
            last_spoken_prediction = None

        # ==================================
        # DISPLAY
        # ==================================

        cv2.rectangle(
            frame,
            (10, 10),
            (700, 220),
            (30, 30, 30),
            -1
        )

        cv2.putText(
            frame,
            "ISL ALPHABET RECOGNIZER V4",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Stable: " + stable_prediction,
            (20, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Current: " + str(current_prediction),
            (20, 125),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Confidence: " + str(round(confidence * 100, 1)) + "%",
            (20, 165),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Hands: " + str(hand_count),
            (20, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # ==================================
        # WORD DISPLAY
        # ==================================

        cv2.rectangle(
            frame,
            (10, 240),
            (700, 310),
            (50, 50, 50),
            -1
        )

        cv2.putText(
            frame,
            "WORD: " + word,
            (20, 285),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "SPACE:Add  BACKSPACE:Delete  ENTER:Clear  S:Save  Q:Quit",
            (10, 350),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1
        )

        cv2.imshow(
            "ISL Alphabet Recognition V4",
            frame
        )

        # ==================================
        # KEYBOARD CONTROLS
        # ==================================

        key = cv2.waitKey(1) & 0xFF

        current_time = time.time()

        if key == ord("q"):
            break

        if current_time - last_key_time >= KEY_DELAY:

            if key == 32:

                if stable_prediction in model.classes_:

                    word += stable_prediction

                    print("Added:", stable_prediction)
                    print("Current word:", word)

                    last_key_time = current_time

            elif key in (8, 127):

                word = word[:-1]

                print("Current word:", word)

                last_key_time = current_time

            elif key in (10, 13):

                word = ""

                print("Word cleared!")

                last_key_time = current_time

            elif key == ord("s"):

                if word:

                    with open(
                        "recognized_words.txt",
                        "a",
                        encoding="utf-8"
                    ) as file:

                        file.write(word + "\n")

                    print("Word saved:", word)

                    # SPEAK COMPLETE WORD

                    speak(word)

                last_key_time = current_time

finally:

    # ======================================
    # 9. CLOSE
    # ======================================

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    # Finish queued speech before closing.

    speech_queue.join()
    speech_queue.put(None)
    speech_thread.join()

    print("\nV4 recognition stopped.")
    print("Final word:", word)