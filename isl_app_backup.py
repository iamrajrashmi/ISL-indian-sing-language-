import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os


# =====================================
# APPLICATION SETTINGS
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

active_process = None
active_name = None


# =====================================
# START RECOGNITION
# =====================================

def start_recognition(filename, name):

    global active_process, active_name

    if active_process is not None:

        if active_process.poll() is None:

            messagebox.showwarning(
                "Already Running",
                "Stop the current recognition before starting another."
            )
            return

    file_path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(file_path):

        messagebox.showerror(
            "File Not Found",
            filename + " was not found!"
        )
        return

    try:

        active_process = subprocess.Popen(
            [sys.executable, file_path],
            cwd=BASE_DIR
        )

        active_name = name

        status_label.config(
            text=name + " is running...",
            fg="green"
        )

    except Exception as error:

        messagebox.showerror(
            "Error",
            str(error)
        )


# =====================================
# STOP RECOGNITION
# =====================================

def stop_recognition():

    global active_process, active_name

    if active_process is not None:

        if active_process.poll() is None:

            active_process.terminate()

            active_process.wait(timeout=5)

        active_process = None
        active_name = None

        status_label.config(
            text="Recognition stopped.",
            fg="red"
        )

    else:

        messagebox.showinfo(
            "Information",
            "No recognition system is running."
        )


# =====================================
# CHECK PROCESS STATUS
# =====================================

def check_process():

    global active_process, active_name

    if active_process is not None:

        if active_process.poll() is not None:

            active_process = None
            active_name = None

            status_label.config(
                text="Recognition finished.",
                fg="blue"
            )

    root.after(1000, check_process)


# =====================================
# CLOSE APPLICATION
# =====================================

def close_application():

    global active_process

    if active_process is not None:

        if active_process.poll() is None:

            active_process.terminate()

            active_process.wait(timeout=5)

    root.destroy()


# =====================================
# MAIN GUI
# =====================================

root = tk.Tk()

root.title("ISL Sign Language Recognition System")

root.geometry("650x550")

root.configure(bg="#202936")

root.resizable(False, False)


# =====================================
# TITLE
# =====================================

title = tk.Label(
    root,
    text="ISL SIGN LANGUAGE",
    font=("Arial", 25, "bold"),
    bg="#202936",
    fg="white"
)

title.pack(pady=(35, 5))


subtitle = tk.Label(
    root,
    text="Recognition and Voice Conversion System",
    font=("Arial", 12),
    bg="#202936",
    fg="#bdc8d6"
)

subtitle.pack(pady=5)


# =====================================
# DIVIDER
# =====================================

divider = tk.Frame(
    root,
    bg="#4d6078",
    height=2,
    width=480
)

divider.pack(pady=25)


# =====================================
# SECTION TITLE
# =====================================

section = tk.Label(
    root,
    text="SELECT RECOGNITION MODE",
    font=("Arial", 14, "bold"),
    bg="#202936",
    fg="white"
)

section.pack(pady=10)


# =====================================
# ALPHABET BUTTON
# =====================================

alphabet_button = tk.Button(
    root,
    text="ALPHABET RECOGNITION  (A-Z)",
    font=("Arial", 13, "bold"),
    bg="#2878b5",
    fg="white",
    activebackground="#1d5e91",
    activeforeground="white",
    width=32,
    height=2,
    cursor="hand2",
    command=lambda: start_recognition(
        "recognize_v4_voice.py",
        "Alphabet Recognition"
    )
)

alphabet_button.pack(pady=15)


# =====================================
# GREETINGS BUTTON
# =====================================

greeting_button = tk.Button(
    root,
    text="GREETING RECOGNITION",
    font=("Arial", 13, "bold"),
    bg="#26866b",
    fg="white",
    activebackground="#19664f",
    activeforeground="white",
    width=32,
    height=2,
    cursor="hand2",
    command=lambda: start_recognition(
        "recognize_greetings_voice.py",
        "Greeting Recognition"
    )
)

greeting_button.pack(pady=15)


# =====================================
# STOP BUTTON
# =====================================

stop_button = tk.Button(
    root,
    text="STOP RECOGNITION",
    font=("Arial", 12, "bold"),
    bg="#b84a4a",
    fg="white",
    activebackground="#963737",
    activeforeground="white",
    width=25,
    height=2,
    cursor="hand2",
    command=stop_recognition
)

stop_button.pack(pady=15)


# =====================================
# STATUS
# =====================================

status_label = tk.Label(
    root,
    text="System Ready",
    font=("Arial", 12, "bold"),
    bg="#202936",
    fg="#55d68b"
)

status_label.pack(pady=20)


# =====================================
# FOOTER
# =====================================

footer = tk.Label(
    root,
    text="Indian Sign Language Recognition Project",
    font=("Arial", 10),
    bg="#202936",
    fg="#bdc8d6"
)

footer.pack(side="bottom", pady=20)


# =====================================
# RUN APPLICATION
# =====================================

root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)

root.after(1000, check_process)

root.mainloop()
