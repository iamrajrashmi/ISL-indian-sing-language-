import cv2
import mediapipe as mp
import csv
import os

# -------------------------------
# 1. MEDIAPIPE SETUP
# -------------------------------

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# -------------------------------
# 2. SELECT ALPHABET
# -------------------------------

label = input("Enter alphabet (A-Z): ").strip().upper()

if len(label) != 1 or label not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    print("Invalid alphabet!")
    raise SystemExit

# -------------------------------
# 3. DATASET SETUP
# -------------------------------

os.makedirs("dataset", exist_ok=True)

csv_path = "dataset/isl_data_2hand_v2.csv"

new_file = (
    not os.path.exists(csv_path)
    or os.path.getsize(csv_path) == 0
)

columns = (
    [f"L{i}" for i in range(63)]
    + [f"R{i}" for i in range(63)]
    + ["Label"]
)

count = 0

# -------------------------------
# 4. OPEN CSV FILE
# -------------------------------

try:

    with open(
        csv_path,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if new_file:
            writer.writerow(columns)

        # -------------------------------
        # 5. HAND DETECTION
        # -------------------------------

        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        ) as hands:

            cap = cv2.VideoCapture(0)

            if not cap.isOpened():
                print("Cannot open webcam!")
                raise SystemExit

            print("\nAlphabet:", label)
            print("SPACE = Save sample")
            print("Q = Exit")

            # -------------------------------
            # 6. MAIN LOOP
            # -------------------------------

            while True:

                success, frame = cap.read()

                if not success:
                    print("Cannot read webcam!")
                    break

                frame = cv2.flip(frame, 1)

                rgb = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                results = hands.process(rgb)

                # Empty features
                left_hand = [0.0] * 63
                right_hand = [0.0] * 63

                detected_hands = 0

                # -------------------------------
                # 7. EXTRACT HAND LANDMARKS
                # -------------------------------

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

                # -------------------------------
                # 8. DISPLAY INFORMATION
                # -------------------------------

                cv2.putText(
                    frame,
                    f"Alphabet: {label}",
                    (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"Hands: {detected_hands}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    f"Samples: {count}",
                    (10, 105),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                cv2.putText(
                    frame,
                    "SPACE = SAVE | Q = EXIT",
                    (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2
                )

                cv2.imshow(
                    "ISL Data Collection",
                    frame
                )

                # -------------------------------
                # 9. KEYBOARD INPUT
                # IMPORTANT: ONLY ONE waitKey()
                # -------------------------------

                key = cv2.waitKey(100) & 0xFF
                if key != 255:
                 print("KEY PRESSED:", key)

                # SPACE BAR
                if key == 32:

                    print("SPACE DETECTED!")

                    if detected_hands > 0:

                        data = left_hand + right_hand

                        writer.writerow(data + [label])

                        file.flush()

                        count += 1

                        print("Sample saved:", count)

                    else:
                        print("No hand detected!")

                # Q KEY
                elif key == ord('q') or key == ord('Q'):

                    print("Closing webcam...")
                    break

            # -------------------------------
            # 10. RELEASE WEBCAM
            # -------------------------------

            cap.release()
            cv2.destroyAllWindows()

except KeyboardInterrupt:

    print("Program stopped.")

print("\nData collection completed!")
print("Samples saved in this session:", count)
print("Dataset location:", csv_path)