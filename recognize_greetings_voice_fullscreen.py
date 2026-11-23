import cv2
import mediapipe as mp
import joblib
import numpy as np
import time
import threading
import queue
import pythoncom
import win32com.client
import ctypes
import os


# =========================================================
# SCREEN AND DISPLAY SETTINGS
# =========================================================

def get_screen_size():
    """Return the Windows display size in pixels."""
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
WINDOW_NAME = "ISL Greeting Recognition - Fullscreen"


def fit_camera_image(frame, target_w, target_h):
    """Fit the camera frame inside its area without cropping."""
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    frame_h, frame_w = frame.shape[:2]

    if frame_h == 0 or frame_w == 0:
        return canvas

    scale = min(target_w / frame_w, target_h / frame_h)
    new_w = max(1, int(frame_w * scale))
    new_h = max(1, int(frame_h * scale))

    resized = cv2.resize(
        frame, (new_w, new_h), interpolation=cv2.INTER_AREA
    )

    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas[y:y + new_h, x:x + new_w] = resized

    return canvas


def draw_panel(
    canvas,
    prediction,
    confidence,
    sequence_count,
    sequence_length,
    detected_frames,
):
    """Draw recognition status and capture progress on the right."""
    x0 = int(CAMERA_W)
    panel_right = int(SCREEN_W)
    screen_h = int(SCREEN_H)

    cv2.rectangle(
        canvas,
        (x0, 0),
        (panel_right, screen_h),
        (27, 32, 43),
        -1,
    )
    cv2.line(
        canvas,
        (x0, 0),
        (x0, screen_h),
        (80, 90, 105),
        2,
    )

    margin = max(22, int(PANEL_W * 0.07))
    x = int(x0 + margin)
    usable_w = int(PANEL_W - 2 * margin)

    scale = max(0.48, min(0.78, PANEL_W / 600))
    line = max(30, int(48 * scale))
    y = max(48, int(screen_h * 0.07))

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

    put("ISL GREETING", y, 0.9, (0, 220, 255), 2)
    put("RECOGNITION", y + line, 0.75, (0, 220, 255), 2)
    y += line * 2 + 25
    divider(y)
    y += line

    put("RECOGNIZED GESTURE", y, 0.55, (170, 185, 205), 1)
    y += int(line * 1.25)
    put(str(prediction).replace("_", " ")[:22], y, 0.78,
        (80, 240, 130), 2)
    y += int(line * 1.45)

    put("CONFIDENCE", y, 0.55, (170, 185, 205), 1)
    y += int(line * 1.15)
    put(f"{float(confidence):.1f}%", y, 0.78)
    y += int(line * 1.4)

    put("GESTURE CAPTURE", y, 0.58, (0, 220, 255), 2)
    y += int(line * 1.1)
    put(
        f"Frames: {sequence_count}/{sequence_length}",
        y,
        0.58,
        (245, 245, 245),
        1,
    )

    bar_y = int(y + line * 0.45)
    bar_h = max(12, int(17 * scale))
    bar_right = int(x + usable_w)

    cv2.rectangle(
        canvas, (x, bar_y), (bar_right, bar_y + bar_h), (65, 70, 82), -1
    )

    progress = min(
        1.0,
        max(0.0, sequence_count / max(1, sequence_length)),
    )
    progress_right = int(x + usable_w * progress)
    cv2.rectangle(
        canvas,
        (x, bar_y),
        (progress_right, bar_y + bar_h),
        (40, 190, 110),
        -1,
    )

    y = int(bar_y + bar_h + line)
    put(f"Frames with hand: {detected_frames}", y, 0.52,
        (210, 215, 225), 1)
    y += int(line * 1.3)
    divider(y)
    y += line

    put("VOICE OUTPUT: ON", y, 0.58, (80, 240, 130), 2)
    y += int(line * 1.25)
    put("HOW TO USE", y, 0.58, (0, 220, 255), 2)
    y += int(line * 0.95)

    instructions = [
        "1. Show one greeting gesture",
        "2. Keep your hand visible",
        "3. Wait for the prediction",
        "4. Remove hand before next",
        "Q  Quit recognition",
    ]

    instruction_size = max(0.40, min(0.51, scale * 0.70))
    instruction_gap = max(25, int(35 * scale))

    for item in instructions:
        if y >= screen_h - 20:
            break

        cv2.putText(
            canvas,
            item,
            (int(x), int(y)),
            cv2.FONT_HERSHEY_SIMPLEX,
            float(instruction_size),
            (225, 230, 238),
            1,
            cv2.LINE_AA,
        )
        y += instruction_gap


# =========================================================
# WINDOWS SPEECH OUTPUT
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


voice_thread = threading.Thread(target=speech_worker, daemon=True)
voice_thread.start()


def speak(text):
    speech_queue.put(str(text))


# =========================================================
# LOAD MODEL
# =========================================================

MODEL_PATH = os.path.join("models", "greeting_model.pkl")

print("Loading Greeting Recognition Model...")

if not os.path.exists(MODEL_PATH):
    print(f"ERROR: Model file not found: {MODEL_PATH}")
    speech_queue.put(None)
    speech_queue.join()
    voice_thread.join(timeout=5)
    raise SystemExit(1)

try:
    model_data = joblib.load(MODEL_PATH)
    model = model_data["model"]
except Exception:
    speech_queue.put(None)
    speech_queue.join()
    voice_thread.join(timeout=5)
    raise

SEQUENCE_LENGTH = 30
FEATURES_PER_FRAME = 126
CONFIDENCE_THRESHOLD = 50

print("Model loaded successfully!")
print("Gestures:", model_data.get("labels", getattr(model, "classes_", [])))


# =========================================================
# MEDIAPIPE SETUP
# =========================================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6,
)


# =========================================================
# LANDMARK EXTRACTION
# =========================================================

def extract_landmarks(results):
    left_hand = np.zeros(63, dtype=float)
    right_hand = np.zeros(63, dtype=float)

    if results.multi_hand_landmarks:
        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness,
        ):
            label = handedness.classification[0].label
            landmarks = []

            for point in hand_landmarks.landmark:
                landmarks.extend([point.x, point.y, point.z])

            if label == "Left":
                left_hand = np.asarray(landmarks, dtype=float)
            else:
                right_hand = np.asarray(landmarks, dtype=float)

    return np.concatenate([left_hand, right_hand])


# =========================================================
# START CAMERA
# =========================================================

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened!")
    hands.close()
    speech_queue.put(None)
    speech_queue.join()
    voice_thread.join(timeout=5)
    raise SystemExit(1)


sequence = []
detected_frames = 0
last_capture_time = 0.0
last_prediction = "Waiting for gesture..."
confidence = 0.0
last_spoken_prediction = None
fullscreen_requested = False

cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

print("\n================================")
print("  ISL GREETING RECOGNITION")
print("================================")
print("Fullscreen display enabled.")
print("Voice output enabled!")
print("Perform one complete greeting gesture.")
print("Each prediction takes approximately 6 seconds.")
print("Remove your hand between different gestures.")
print("Press Q to quit.")
print("================================\n")


# =========================================================
# MAIN LOOP
# =========================================================

try:
    while True:
        success, frame = cap.read()

        if not success:
            print("Camera error!")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                )

        current_time = time.time()

        if current_time - last_capture_time >= 0.2:
            landmarks = extract_landmarks(results)
            sequence.append(landmarks)

            if np.any(landmarks):
                detected_frames += 1

            last_capture_time = current_time

        if len(sequence) >= SEQUENCE_LENGTH:
            if detected_frames >= 5:
                input_data = np.asarray(sequence[:SEQUENCE_LENGTH])
                input_data = input_data.flatten().reshape(1, -1)

                probabilities = model.predict_proba(input_data)[0]
                best_index = int(np.argmax(probabilities))
                prediction = model.classes_[best_index]
                new_confidence = float(probabilities[best_index] * 100)

                if new_confidence >= CONFIDENCE_THRESHOLD:
                    last_prediction = str(prediction)
                    confidence = new_confidence

                    print(
                        f"Detected: {prediction} "
                        f"| Confidence: {confidence:.1f}%"
                    )

                    if prediction != last_spoken_prediction:
                        spoken_text = str(prediction).replace("_", " ")
                        speak(spoken_text)
                        last_spoken_prediction = prediction
                else:
                    last_prediction = "Uncertain gesture"
                    confidence = new_confidence
                    last_spoken_prediction = None
            else:
                last_prediction = "Hand not detected properly"
                confidence = 0.0
                last_spoken_prediction = None

            sequence.clear()
            detected_frames = 0

        camera_image = fit_camera_image(frame, CAMERA_W, SCREEN_H)
        screen = np.zeros((SCREEN_H, SCREEN_W, 3), dtype=np.uint8)
        screen[:, :CAMERA_W] = camera_image

        draw_panel(
            screen,
            last_prediction,
            confidence,
            len(sequence),
            SEQUENCE_LENGTH,
            detected_frames,
        )

        cv2.imshow(WINDOW_NAME, screen)

        # Request fullscreen after OpenCV has created and displayed the window.
        if not fullscreen_requested:
            cv2.setWindowProperty(
                WINDOW_NAME,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN,
            )
            fullscreen_requested = True

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    hands.close()
    cv2.destroyAllWindows()

    # Stop the speech worker, then wait for all queued speech to finish.
    speech_queue.put(None)
    speech_queue.join()
    voice_thread.join(timeout=10)

    print("\nRecognition stopped.")