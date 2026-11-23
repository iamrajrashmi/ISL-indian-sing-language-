import subprocess
import sys
import os

while True:

    print("\n================================")
    print("       ISL RECOGNITION APP")
    print("================================")
    print("1. Alphabet Recognition")
    print("2. Greeting Recognition")
    print("Q. Exit")
    print("================================")

    choice = input("Enter your choice: ").strip().lower()

    if choice == "1":

        print("\nStarting Alphabet Recognition...")
        subprocess.run([sys.executable, "recognize.py"])

    elif choice == "2":

        print("\nStarting Greeting Recognition...")
        subprocess.run([sys.executable, "recognize_greetings.py"])

    elif choice == "q":

        print("\nApplication closed.")
        break

    else:

        print("\nInvalid choice. Try again.")