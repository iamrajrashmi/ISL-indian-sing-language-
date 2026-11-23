import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import time

# ==========================================
# SETTINGS
# ==========================================

DATASET_PATH = "dataset/isl_alphabet_v3.csv"

SAMPLES_PER_ALPHABET = 100
SAMPLE_INTERVAL = 0.10
COUNTDOWN_SECONDS = 3

FEATURES_PER_HAND = 63
FEATURES_PER_FRAME = 126

# ==========================================
# CREATE FOLDERS
# ==========================================

os.makedirs("dataset", exist_ok=True)

columns = (
    [f"L{i}" for i in range(63)] +
    [f"R{i}" for i in range(63)] +
    ["Label"]
)

if not os.path.exists(DATASET_PATH):
    pd.DataFrame(columns=columns).to_csv(
        DATASET_PATH, index=False
    )

# ==========================================
# MEDIAPIPE
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
# EXTRACT HAND FEATURES
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
# COLLECTION FUNCTION
# ==========================================

def collect_alphabet(label):

    print("\nPreparing alphabet:", label)

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Webcam could not be opened.")
        return

    captured_samples = []
    recording = False
    countdown_start = None
    last_sample_time = 0

    print("\nShow the ISL sign for", label)
    print("Press SPACE to start collection.")
    print("Press Q to cancel.")

    while True:

        success, frame = cap.read()

        if not success:
            print("Camera frame could not be read.")
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        results = hands.process(rgb)

        hand_count = 0

        if results.multi_hand_landmarks:

            hand_count = len(
                results.multi_hand_landmarks
            )

            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

        # ==================================
        # START COUNTDOWN
        # ==================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == 32 and not recording:

            recording = True
            countdown_start = time.time()

        # ==================================
        # COUNTDOWN
        # ==================================

        if recording and len(captured_samples) == 0:

            elapsed = time.time() - countdown_start

            remaining = COUNTDOWN_SECONDS - int(elapsed)

            if remaining > 0:

                cv2.putText(
                    frame,
                    "GET READY: " + str(remaining),
                    (30, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 255, 255),
                    3
                )

            else:

                last_sample_time = 0.0
                countdown_start = None

        # ==================================
        # CAPTURE SAMPLES
        # ==================================

        if recording and countdown_start is None:

            if hand_count > 0:

                current_time = time.time()

                if (
                    current_time - last_sample_time
                    >= SAMPLE_INTERVAL
                ):

                    features = extract_features(results)

                    captured_samples.append(
                        features + [label]
                    )

                    last_sample_time = current_time

            cv2.putText(
                frame,
                f"Samples: {len(captured_samples)}/{SAMPLES_PER_ALPHABET}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            if len(captured_samples) >= SAMPLES_PER_ALPHABET:
                break

        # ==================================
        # DISPLAY
        # ==================================

        cv2.putText(
            frame,
            "ALPHABET: " + label,
            (20, 440),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Hands detected: " + str(hand_count),
            (20, 475),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow("ISL Alphabet V3 Collection", frame)

    cap.release()
    cv2.destroyAllWindows()

    # ======================================
    # SAVE DATA
    # ======================================

    if captured_samples:

        new_data = pd.DataFrame(
            captured_samples,
            columns=columns
        )

        new_data.to_csv(
            DATASET_PATH,
            mode="a",
            header=False,
            index=False
        )

        print("\nCollection completed!")
        print("Alphabet:", label)
        print("Samples saved:", len(captured_samples))

    else:

        print("\nNo samples collected for", label)


# ==========================================
# MAIN PROGRAM
# ==========================================

print("=" * 45)
print("ISL ALPHABET V3 - FRESH DATA COLLECTION")
print("=" * 45)

print("\nDataset:", DATASET_PATH)
print("Samples per alphabet:", SAMPLES_PER_ALPHABET)

while True:

    label = input(
        "\nEnter alphabet A-Z (or DONE to finish): "
    ).strip().upper()

    if label == "DONE":
        break

    if len(label) != 1 or label not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        print("Invalid input. Enter one alphabet from A to Z.")
        continue

    collect_alphabet(label)

print("\nCollection session finished.")

if os.path.exists(DATASET_PATH):

    data = pd.read_csv(DATASET_PATH)

    print("\nCurrent dataset counts:")
    print(data["Label"].value_counts().sort_index())

    print("\nTotal samples:", len(data))

hands.close()

print("\nNew dataset saved successfully!")