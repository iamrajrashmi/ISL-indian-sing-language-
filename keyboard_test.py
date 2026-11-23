import cv2
import numpy as np

window = np.zeros((400, 600, 3), dtype=np.uint8)

cv2.namedWindow("Keyboard Test")

print("Click the black window and press SPACE or Q.")

while True:

    cv2.imshow("Keyboard Test", window)

    key = cv2.waitKeyEx(30)

    if key != -1:
        print("Key detected:", key)

    if (key & 0xFF) == 32:
        print("SPACE IS WORKING!")

    elif (key & 0xFF) == ord('q'):
        print("Q IS WORKING!")
        break

cv2.destroyAllWindows()