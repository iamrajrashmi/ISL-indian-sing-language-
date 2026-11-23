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
import ctypes

from collections import deque, Counter


# =========================================================
# FULLSCREEN DISPLAY SETTINGS
# =========================================================

def get_screen_size():
    """Get the Windows display size in pixels."""
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        width = ctypes.windll.user32.GetSystemMetrics(0)
        height = ctypes.windll.user32.GetSystemMetrics(1)
        if width > 0 and height > 0:
            return width, height
    except Exception:
        pass

    return 1920, 1080


SCREEN_W, SCREEN_H = get_screen_size()
PANEL_W = max(360, int(SCREEN_W * 0.27))
CAMERA_W = SCREEN_W - PANEL_W
WINDOW_NAME = "ISL Alphabet Recognition V4 - Fullscreen"


def fit_camera_image(frame, target_w, target_h):
    """Resize camera image proportionally without cropping it."""
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    h, w = frame.shape[:2]

    if h == 0 or w == 0:
        return canvas

    scale = min(target_w / w, target_h / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))

    resized = cv2.resize(
        frame, (new_w, new_h), interpolation=cv2.INTER_AREA
    )
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas[y:y + new_h, x:x + new_w] = resized

    return canvas


def draw_panel(canvas, stable, current, confidence, hand_count, word):
    """Draw information in the right-side panel."""
    x0 = int(CAMERA_W)
    margin = max(22, int(PANEL_W * 0.07))
    x = int(x0 + margin)
    usable_w = int(PANEL_W - 2 * margin)

    scale = max(0.48, min(0.78, PANEL_W / 600))
    line = max(30, int(48 * scale))
    y = max(48, int(SCREEN_H * 0.07))

    cv2.rectangle(
        canvas, (x0, 0), (int(SCREEN_W), int(SCREEN_H)), (27, 32, 43), -1
    )
    cv2.line(
        canvas, (x0, 0), (x0, int(SCREEN_H)), (80, 90, 105), 2
    )

    def put(text, yy, size=0.65, color=(240, 240, 240), thickness=2):
        cv2.putText(
            canvas,
            str(text),
            (int(x), int(yy)),
            cv2.FONT_HERSHEY_SIMPLEX,
            float(size * scale / 0.65),
            color,
            int(thickness),
            cv2.LINE_AA,
        )

    def divider(yy):
        yy = int(yy)
        cv2.line(
            canvas,
            (int(x), yy),
            (int(x + usable_w), yy),
            (90, 100, 115),
            1,
        )

    put("ISL ALPHABET", y, 0.9, (0, 220, 255), 2)
    put("RECOGNITION V4", y + line, 0.75, (0, 220, 255), 2)
    y += line * 2 + 25
    divider(y)
    y += line

    put("STABLE LETTER", y, 0.55, (170, 185, 205), 1)
    y += int(line * 1.25)
    put(stable, y, 0.9, (80, 240, 130), 2)
    y += int(line * 1.5)

    put("CURRENT PREDICTION", y, 0.55, (170, 185, 205), 1)
    y += int(line * 1.15)
    put(current, y, 0.72)
    y += int(line * 1.35)

    put("CONFIDENCE", y, 0.55, (170, 185, 205), 1)
    y += int(line * 1.1)
    put(f"{confidence * 100:.1f}%", y, 0.75)
    y += int(line * 1.25)

    put(f"HANDS DETECTED: {hand_count}", y, 0.58)
    y += int(line * 1.2)
    divider(y)
    y += line

    put("WORD FORMATION", y, 0.58, (0, 220, 255), 2)
    y += int(line * 1.2)

    display_word = word if word else "(empty)"
    max_chars = max(10, int(usable_w / max(12, 22 * scale)))

    for i in range(0, len(display_word), max_chars):
        if y >= SCREEN_H - 40:
            break
        put(display_word[i:i + max_chars], y, 0.72, (0, 230, 255), 2)
        y += int(line * 0.95)

    y += int(line * 0.55)
    divider(y)
    y += line

    put("VOICE OUTPUT: ON", y, 0.58, (80, 240, 130), 2)
    y += int(line * 1.2)
    put("KEYBOARD CONTROLS", y, 0.58, (0, 220, 255), 2)
    y += int(line * 0.95)

    controls = [
        "SPACE  Add stable letter",
        "BACKSPACE  Delete letter",
        "ENTER  Clear word",
        "S  Save and speak word",
        "Q  Quit recognition",
    ]

    control_size = max(0.40, min(0.53, scale * 0.72))
    control_gap = max(25, int(35 * scale))

    for item in controls:
        if y >= SCREEN_H - 20:
            break
        cv2.putText(
            canvas,
            item,
            (int(x), int(y)),
            cv2.FONT_HERSHEY_SIMPLEX,
            float(control_size),
            (225, 230, 238),
            1,
            cv2.LINE_AA,
        )
        y += control_gap


# =========================================================
# LOAD V4 MODEL
# =========================================================

MODEL_PATH = os.path.join("models", "isl_alphabet_model_v4.pkl")

print("Loading ISL Alphabet V4 Model...")

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: V4 model not found: {MODEL_PATH}")
    raise SystemExit(1)

model = joblib.load(MODEL_PATH)

if hasattr(model, "n_jobs"):
    model.n_jobs = 1

print("Model loaded successfully!")
print("Alphabets:", model.classes_)


# =========================================================
# WINDOWS VOICE OUTPUT
# =========================================================

speech_queue = queue.Queue()


def speech_worker():
    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Rate = 0
        speaker.Volume = 100

        while True:
            text = speech_queue.get()
            try:
                if text is None:
                    break

                try:
                    print("Speaking:", text)
                    speaker.Speak(str(text))
                except Exception as error:
                    print("Voice error:", error)
            finally:
                speech_queue.task_done()
    finally:
        pythoncom.CoUninitialize()


speech_thread = threading.Thread(target=speech_worker, daemon=True)
speech_thread.start()


def speak(text):
    speech_queue.put(str(text))


print("Alphabet voice output enabled!")


# =========================================================
# MEDIAPIPE
# =========================================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)


# =========================================================
# RECOGNITION SETTINGS
# =========================================================

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


# =========================================================
# NORMALIZE ONE HAND
# =========================================================

def normalize_hand(values):
    values = np.asarray(values, dtype=float)

    if np.all(values == 0):
        return [0.0] * 63

    points = values.reshape(21, 3)
    points = points - points[0]

    scale = np.max(np.linalg.norm(points, axis=1))
    if scale > 0:
        points = points / scale

    return points.flatten().tolist()


# =========================================================
# EXTRACT FEATURES
# =========================================================

def extract_features(results):
    left_hand = [0.0] * 63
    right_hand = [0.0] * 63

    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = (
                results.multi_handedness[i].classification[0].label
            )

            values = []
            for landmark in hand_landmarks.landmark:
                values.extend([landmark.x, landmark.y, landmark.z])

            if handedness == "Left":
                left_hand = values
            else:
                right_hand = values

    left_hand = normalize_hand(left_hand)
    right_hand = normalize_hand(right_hand)

    return left_hand + right_hand


# =========================================================
# START WEBCAM
# =========================================================

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened!")
    hands.close()
    speech_queue.put(None)
    speech_queue.join()
    speech_thread.join()
    raise SystemExit(1)

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(
    WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
)

print("\n==================================")
print("ISL ALPHABET RECOGNITION V4")
print("Fullscreen display enabled.")
print("SPACE     = Add stable letter")
print("BACKSPACE = Delete last letter")
print("ENTER     = Clear word")
print("S         = Save and speak word")
print("Q         = Quit")
print("==================================")


# =========================================================
# MAIN LOOP
# =========================================================

try:
    while True:
        success, frame = cap.read()

        if not success:
            print("Unable to read webcam.")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        hand_count = 0
        current_prediction = "NO HAND"
        confidence = 0.0
        stable_prediction = "WAITING"

        if results.multi_hand_landmarks:
            hand_count = len(results.multi_hand_landmarks)

            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

            features = extract_features(results)

            if not hasattr(model, "feature_names_in_"):
                raise AttributeError(
                    "The loaded model has no feature_names_in_. "
                    "Check that this is the correct trained model."
                )

            input_data = pd.DataFrame(
                [features], columns=model.feature_names_in_
            )

            probabilities = model.predict_proba(input_data)[0]
            best_index = int(np.argmax(probabilities))
            current_prediction = model.classes_[best_index]
            confidence = float(probabilities[best_index])

            prediction_history.append((current_prediction, confidence))
            labels = [item[0] for item in prediction_history]
            counts = Counter(labels)
            selected_label, selected_count = counts.most_common(1)[0]

            if selected_count >= REQUIRED_COUNT:
                selected_confidences = [
                    conf for label, conf in prediction_history
                    if label == selected_label
                ]
                average_confidence = float(np.mean(selected_confidences))

                if average_confidence >= CONFIDENCE_THRESHOLD:
                    stable_prediction = selected_label
                    confidence = average_confidence
                else:
                    stable_prediction = "UNCERTAIN"
            else:
                stable_prediction = "STABILIZING"

            if stable_prediction in model.classes_:
                if stable_prediction != last_spoken_prediction:
                    speak(stable_prediction)
                    last_spoken_prediction = stable_prediction
        else:
            prediction_history.clear()
            last_spoken_prediction = None

        camera_image = fit_camera_image(frame, CAMERA_W, SCREEN_H)
        screen = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
        screen[:, :CAMERA_W] = camera_image

        draw_panel(
            screen,
            stable_prediction,
            current_prediction,
            confidence,
            hand_count,
            word,
        )

        cv2.imshow(WINDOW_NAME, screen)

        key = cv2.waitKey(1) & 0xFF
        current_time = time.time()

        if key == ord("q"):
            break

        if current_time - last_key_time >= KEY_DELAY:
            if key == 32:
                if stable_prediction in model.classes_:
                    word += str(stable_prediction)
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
                        "recognized_words.txt", "a", encoding="utf-8"
                    ) as file:
                        file.write(word + "\n")

                    print("Word saved:", word)
                    speak(word)

                last_key_time = current_time

finally:
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

    # Send the stop signal first, then wait for the worker to finish.
    speech_queue.put(None)
    speech_queue.join()
    speech_thread.join()

    print("\nV4 recognition stopped.")
    print("Final word:", word)