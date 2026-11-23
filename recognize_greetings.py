import cv2
import mediapipe as mp
import joblib
import numpy as np
import time
import pyttsx3
import threading
import queue

# =====================================
# 1. VOICE SYSTEM
# =====================================

speech_queue = queue.Queue()

def speech_worker():

    engine = pyttsx3.init()

    engine.setProperty("rate", 145)
    engine.setProperty("volume", 1.0)

    while True:

        text = speech_queue.get()

        if text is None:
            break

        try:
            engine.say(text)
            engine.runAndWait()

        except Exception as error:
            print("Voice error:", error)

        speech_queue.task_done()

    engine.stop()


voice_thread = threading.Thread(
    target=speech_worker,
    daemon=True
)

voice_thread.start()


def speak(text):
    speech_queue.put(text)


# =====================================
# 2. LOAD MODEL
# =====================================

print("Loading Greeting Recognition Model...")

model_data = joblib.load("models/greeting_model.pkl")

model = model_data["model"]

SEQUENCE_LENGTH = 30
FEATURES_PER_FRAME = 126

CONFIDENCE_THRESHOLD = 50

print("Model loaded successfully!")
print("Gestures:", model_data["labels"])


# =====================================
# 3. MEDIAPIPE SETUP
# =====================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)


# =====================================
# 4. LANDMARK EXTRACTION
# =====================================

def extract_landmarks(results):

    left_hand = np.zeros(63)
    right_hand = np.zeros(63)

    if results.multi_hand_landmarks:

        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):

            label = handedness.classification[0].label

            landmarks = []

            for point in hand_landmarks.landmark:

                landmarks.extend([
                    point.x,
                    point.y,
                    point.z
                ])

            if label == "Left":
                left_hand = np.array(landmarks)

            else:
                right_hand = np.array(landmarks)

    return np.concatenate([left_hand, right_hand])


# =====================================
# 5. CAMERA SETUP
# =====================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Webcam could not be opened!")

    hands.close()
    speech_queue.put(None)
    raise SystemExit


sequence = []

detected_frames = 0

last_capture_time = 0

last_prediction = "Waiting for gesture..."

confidence = 0.0

last_spoken_prediction = None


print("\n================================")
print("  ISL GREETING RECOGNITION")
print("================================")
print("Voice output enabled!")
print("Perform one complete greeting gesture.")
print("Each prediction takes approximately 6 seconds.")
print("Remove your hand between different gestures.")
print("Press Q to quit.")
print("================================\n")


# =====================================
# 6. MAIN LOOP
# =====================================

while True:

    success, frame = cap.read()

    if not success:

        print("Camera error!")
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = hands.process(rgb)

    # =================================
    # DRAW LANDMARKS
    # =================================

    if results.multi_hand_landmarks:

        for hand_landmarks in results.multi_hand_landmarks:

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    current_time = time.time()

    # =================================
    # 7. CAPTURE FRAMES
    # =================================

    if current_time - last_capture_time >= 0.2:

        landmarks = extract_landmarks(results)

        sequence.append(landmarks)

        if np.any(landmarks):
            detected_frames += 1

        last_capture_time = current_time

    # =================================
    # 8. PREDICTION
    # =================================

    if len(sequence) >= SEQUENCE_LENGTH:

        if detected_frames >= 5:

            input_data = np.array(
                sequence[:SEQUENCE_LENGTH]
            )

            input_data = input_data.flatten()

            input_data = input_data.reshape(1, -1)

            probabilities = model.predict_proba(
                input_data
            )[0]

            best_index = np.argmax(probabilities)

            prediction = model.classes_[best_index]

            new_confidence = probabilities[best_index] * 100

            if new_confidence >= CONFIDENCE_THRESHOLD:

                last_prediction = prediction

                confidence = new_confidence

                print(
                    f"Detected: {prediction} "
                    f"| Confidence: {confidence:.1f}%"
                )

                # Speak only once for the same continuous gesture

                if prediction != last_spoken_prediction:

                    spoken_text = str(prediction).replace(
                        "_", " "
                    )

                    speak(spoken_text)

                    print("Speaking:", spoken_text)

                    last_spoken_prediction = prediction

            else:

                last_prediction = "Uncertain gesture"

                confidence = new_confidence

                last_spoken_prediction = None

        else:

            last_prediction = "Hand not detected properly"

            confidence = 0.0

            last_spoken_prediction = None

        # Start a fresh sequence

        sequence.clear()

        detected_frames = 0

    # =================================
    # 9. DISPLAY RESULT
    # =================================

    cv2.rectangle(
        frame,
        (10, 10),
        (650, 160),
        (30, 30, 30),
        -1
    )

    cv2.putText(
        frame,
        "ISL GREETING RECOGNITION",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Gesture: " + last_prediction,
        (20, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
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
        f"Recording: {len(sequence)}/{SEQUENCE_LENGTH}",
        (20, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "VOICE OUTPUT: ON",
        (20, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "Press Q to Quit",
        (20, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "Stable ISL Greeting Recognition",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =====================================
# 10. CLEANUP
# =====================================

cap.release()

hands.close()

cv2.destroyAllWindows()

speech_queue.put(None)

voice_thread.join(timeout=5)

print("\nRecognition stopped.")