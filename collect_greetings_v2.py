import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import time

# ==========================================
# SETTINGS
# ==========================================

DATASET_PATH = "dataset/greeting_sequences_v2.csv"

SEQUENCE_LENGTH = 30
FEATURES_PER_FRAME = 126

RECORD_SECONDS = 6
COUNTDOWN_SECONDS = 3

MIN_VALID_FRAMES = 24

LABELS = {
    ord("1"): "HELLO",
    ord("2"): "GOOD_MORNING",
    ord("3"): "GOOD_AFTERNOON",
    ord("4"): "GOOD_EVENING",
    ord("5"): "GOOD_NIGHT",
    ord("6"): "BYE"
}

os.makedirs("dataset", exist_ok=True)

# ==========================================
# MEDIAPIPE
# ==========================================

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.65,
    min_tracking_confidence=0.65
)

# ==========================================
# LANDMARK EXTRACTION
# ==========================================

def extract_landmarks(results):

    left_hand = np.zeros(63)
    right_hand = np.zeros(63)

    if results.multi_hand_landmarks:

        for hand_landmarks, handedness in zip(
            results.multi_hand_landmarks,
            results.multi_handedness
        ):

            label = handedness.classification[0].label

            values = []

            for point in hand_landmarks.landmark:

                values.extend([
                    point.x,
                    point.y,
                    point.z
                ])

            if label == "Left":
                left_hand = np.array(values)

            else:
                right_hand = np.array(values)

    return np.concatenate([left_hand, right_hand])


# ==========================================
# SAVE DATA
# ==========================================

def save_sample(sequence, label):

    columns = [
        f"F{frame}_{feature}"
        for frame in range(SEQUENCE_LENGTH)
        for feature in range(FEATURES_PER_FRAME)
    ]

    row = np.array(sequence).flatten().tolist()

    new_data = pd.DataFrame(
        [row + [label]],
        columns=columns + ["Label"]
    )

    if os.path.exists(DATASET_PATH):

        new_data.to_csv(
            DATASET_PATH,
            mode="a",
            header=False,
            index=False
        )

    else:

        new_data.to_csv(
            DATASET_PATH,
            index=False
        )

    print("\nSample saved successfully!")
    print("Gesture:", label)
    print("Dataset:", DATASET_PATH)


# ==========================================
# CAMERA
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Webcam could not be opened!")

    hands.close()
    exit()

# ==========================================
# VARIABLES
# ==========================================

selected_label = None
selected_style = None

sample_counts = {}

if os.path.exists(DATASET_PATH):

    old_data = pd.read_csv(DATASET_PATH)

    if "Label" in old_data.columns:
        sample_counts = old_data["Label"].value_counts().to_dict()

# ==========================================
# INSTRUCTIONS
# ==========================================

print("\n==========================================")
print("       IMPROVED GREETING COLLECTION")
print("==========================================")

print("1 = HELLO")
print("2 = GOOD_MORNING")
print("3 = GOOD_AFTERNOON")
print("4 = GOOD_EVENING")
print("5 = GOOD_NIGHT")
print("6 = BYE")

print("\nM = Continuous movement style")
print("H = Perform once and hold final position")

print("\nSPACE = Start recording")
print("Q = Quit")

print("\nEach recording takes 6 seconds.")
print("At least 24 of 30 frames must contain a hand.")
print("==========================================\n")


# ==========================================
# MAIN LOOP
# ==========================================

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

            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    # ======================================
    # DISPLAY INSTRUCTIONS
    # ======================================

    cv2.rectangle(
        frame,
        (5, 5),
        (750, 210),
        (30, 30, 30),
        -1
    )

    cv2.putText(
        frame,
        "GREETING DATA COLLECTION V2",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "1 HELLO  2 MORNING  3 AFTERNOON",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "4 EVENING  5 NIGHT  6 BYE",
        (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "M = Movement | H = Hold | SPACE = Record",
        (20, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "Q = Quit",
        (20, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    label_text = selected_label or "Not selected"
    style_text = selected_style or "Not selected"

    cv2.putText(
        frame,
        "LABEL: " + label_text,
        (20, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "STYLE: " + style_text,
        (20, 305),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.imshow("Greeting Collection V2", frame)

    key = cv2.waitKey(1) & 0xFF

    # ======================================
    # QUIT
    # ======================================

    if key == ord("q") or key == ord("Q"):
        break

    # ======================================
    # SELECT GREETING
    # ======================================

    if key in LABELS:

        selected_label = LABELS[key]

        print("\nSelected greeting:", selected_label)

    # ======================================
    # SELECT RECORDING STYLE
    # ======================================

    if key == ord("m") or key == ord("M"):

        selected_style = "MOVEMENT"

        print("Movement style selected.")

    if key == ord("h") or key == ord("H"):

        selected_style = "HOLD"

        print("Hold style selected.")

    # ======================================
    # START RECORDING
    # ======================================

    if key == ord(" "):

        if selected_label is None:

            print("Please select a greeting first.")
            continue

        if selected_style is None:

            print("Please select M or H recording style.")
            continue

        print("\nGet ready:", selected_label)
        print("Recording style:", selected_style)

        # Countdown

        for count in range(COUNTDOWN_SECONDS, 0, -1):

            success, countdown_frame = cap.read()

            if not success:
                break

            countdown_frame = cv2.flip(countdown_frame, 1)

            cv2.putText(
                countdown_frame,
                "GET READY: " + selected_label,
                (30, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                countdown_frame,
                str(count),
                (250, 200),
                cv2.FONT_HERSHEY_SIMPLEX,
                4,
                (0, 255, 0),
                5
            )

            cv2.imshow(
                "Greeting Collection V2",
                countdown_frame
            )

            if cv2.waitKey(1000) & 0xFF == ord("q"):
                break

        # ==================================
        # RECORD 30 FRAMES
        # ==================================

        sequence = []
        detected_frames = 0

        recording_start = time.time()

        for i in range(SEQUENCE_LENGTH):

            target_time = (
                i * RECORD_SECONDS / SEQUENCE_LENGTH
            )

            while time.time() - recording_start < target_time:

                success, frame = cap.read()

                if not success:
                    break

                frame = cv2.flip(frame, 1)

                cv2.imshow(
                    "Greeting Collection V2",
                    frame
                )

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if not success:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = hands.process(rgb)

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:

                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

            landmarks = extract_landmarks(results)

            if np.any(landmarks):
                detected_frames += 1

            sequence.append(landmarks)

            cv2.putText(
                frame,
                "RECORDING: " + selected_label,
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Frames: {i + 1}/30",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Hands detected: {detected_frames}",
                (20, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 0),
                2
            )

            cv2.imshow(
                "Greeting Collection V2",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # ==================================
        # CHECK AND SAVE
        # ==================================

        if len(sequence) == SEQUENCE_LENGTH:

            if detected_frames >= MIN_VALID_FRAMES:

                save_sample(sequence, selected_label)

                sample_counts[selected_label] = (
                    sample_counts.get(selected_label, 0) + 1
                )

                print(
                    "Samples collected for",
                    selected_label,
                    ":",
                    sample_counts[selected_label]
                )

            else:

                print("\nRECORDING REJECTED!")

                print(
                    "Only",
                    detected_frames,
                    "valid frames detected."
                )

                print(
                    "At least",
                    MIN_VALID_FRAMES,
                    "are required."
                )

                print("Please try again.")

        else:

            print("\nRecording interrupted. Nothing saved.")

        print("\nSelect another greeting or record again.")


# ==========================================
# CLEANUP
# ==========================================

cap.release()

hands.close()

cv2.destroyAllWindows()

print("\nCollection session completed!")