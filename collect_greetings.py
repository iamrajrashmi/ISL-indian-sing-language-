import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import time

# =====================================
# SETTINGS
# =====================================

LABEL = "BYE"

DATASET_PATH = "dataset/greeting_sequences.csv"

SEQUENCE_LENGTH = 30
FEATURES_PER_HAND = 63
FEATURES_PER_FRAME = 126

RECORD_SECONDS = 6
COUNTDOWN_SECONDS = 3

os.makedirs("dataset", exist_ok=True)

# =====================================
# MEDIAPIPE SETUP
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
# LANDMARK EXTRACTION
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
# CAMERA SETUP
# =====================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Webcam could not be opened.")
    exit()

print("\n================================")
print("      BYE GESTURE COLLECTION")
print("================================")
print("Perform the BYE gesture.")
print("Press SPACE to start recording.")
print("Press Q to quit.")
print("Each sample takes 6 seconds.")
print("================================\n")

# =====================================
# MAIN LOOP
# =====================================

while True:

    success, frame = cap.read()

    if not success:
        print("Camera frame error.")
        break

    frame = cv2.flip(frame, 1)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )

    cv2.putText(
        frame,
        "LABEL: BYE",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        "SPACE = Record | Q = Quit",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.imshow("BYE Gesture Collection", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    # =================================
    # START RECORDING
    # =================================

    if key == ord(" "):

        print("\nGet ready for BYE gesture...")

        # Countdown
        for count in range(COUNTDOWN_SECONDS, 0, -1):

            start_frame = np.zeros((200, 500, 3), dtype=np.uint8)

            cv2.putText(
                start_frame,
                str(count),
                (220, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                4,
                (0, 255, 0),
                5
            )

            cv2.imshow("Countdown", start_frame)
            cv2.waitKey(1000)

        cv2.destroyWindow("Countdown")

        print("Recording started! Perform BYE continuously.")

        sequence = []
        detected_frames = 0

        recording_start = time.time()
        next_frame = 0

        # =================================
        # CAPTURE 30 FRAMES OVER 6 SECONDS
        # =================================

        while next_frame < SEQUENCE_LENGTH:

            success, frame = cap.read()

            if not success:
                break

            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = hands.process(rgb)

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

            elapsed = time.time() - recording_start

            target_time = (
                next_frame * RECORD_SECONDS / SEQUENCE_LENGTH
            )

            if elapsed >= target_time:

                landmarks = extract_landmarks(results)

                if np.any(landmarks):
                    detected_frames += 1

                sequence.extend(landmarks.tolist())

                next_frame += 1

            cv2.putText(
                frame,
                "RECORDING BYE",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            cv2.putText(
                frame,
                f"Frames: {next_frame}/{SEQUENCE_LENGTH}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.imshow("BYE Gesture Collection", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # =================================
        # SAVE SAMPLE
        # =================================

        if next_frame == SEQUENCE_LENGTH:

            if detected_frames >= 5:

                row = sequence + [LABEL]

                columns = [
                    f"f{i}" for i in range(
                        SEQUENCE_LENGTH * FEATURES_PER_FRAME
                    )
                ]

                columns.append("Label")

                new_data = pd.DataFrame(
                    [row],
                    columns=columns
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

                print("\nBYE gesture saved successfully!")
                print("Frames captured:", next_frame)
                print("Frames with hands:", detected_frames)

            else:

                print("\nNot enough hand landmarks detected.")
                print("Please keep your hand visible and try again.")

        else:
            print("\nRecording interrupted. Sample not saved.")

        print("\nPress SPACE to record another BYE sample.")

# =====================================
# CLEANUP
# =====================================

cap.release()
hands.close()
cv2.destroyAllWindows()

print("\nBYE collection session completed!")