import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import sys
import os
import threading
import queue
import csv
from datetime import datetime


# =====================================
# APPLICATION SETTINGS
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = os.path.join(
    BASE_DIR,
    "recognition_history.csv"
)

active_process = None
active_name = None

output_queue = queue.Queue()


# =====================================
# CREATE HISTORY FILE
# =====================================

def create_history_file():

    if not os.path.exists(HISTORY_FILE):

        with open(
            HISTORY_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date and Time",
                "Recognition Type",
                "Recognized Result",
                "Details"
            ])


# =====================================
# SAVE RECOGNITION HISTORY
# =====================================

def save_history(mode, line):

    event_type = None
    result = ""
    details = ""

    if mode == "Alphabet Recognition":

        if line.startswith("Added:"):

            event_type = "Alphabet"
            result = line.split(":", 1)[1].strip()

        elif line.startswith("Word saved:"):

            event_type = "Word"
            result = line.split(":", 1)[1].strip()

    elif mode == "Greeting Recognition":

        if line.startswith("Detected:"):

            event_type = "Greeting"

            parts = line.split("|", 1)

            result = parts[0].replace(
                "Detected:", ""
            ).strip()

            if len(parts) > 1:

                details = parts[1].strip()

    if event_type is not None:

        timestamp = datetime.now().strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )

        with open(
            HISTORY_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                timestamp,
                event_type,
                result,
                details
            ])

        print("History saved:", result)


# =====================================
# READ RECOGNITION OUTPUT
# =====================================

def read_output(process, mode):

    try:

        for line in process.stdout:

            output_queue.put(
                (line.rstrip(), mode)
            )

    except Exception as error:

        output_queue.put(
            ("Output error: " + str(error), mode)
        )


# =====================================
# DISPLAY OUTPUT
# =====================================

def update_output():

    while not output_queue.empty():

        message, mode = output_queue.get()

        output_box.config(state="normal")

        output_box.insert(
            tk.END,
            message + "\n"
        )

        output_box.see(tk.END)

        output_box.config(state="disabled")

        save_history(mode, message)

    root.after(100, update_output)


def clear_output():

    output_box.config(state="normal")

    output_box.delete("1.0", tk.END)

    output_box.config(state="disabled")


# =====================================
# START RECOGNITION
# =====================================

def start_recognition(filename, name):

    global active_process, active_name

    if active_process is not None:

        if active_process.poll() is None:

            messagebox.showwarning(
                "Already Running",
                "Stop the current recognition first."
            )

            return

    file_path = os.path.join(BASE_DIR, filename)

    if not os.path.exists(file_path):

        messagebox.showerror(
            "File Not Found",
            filename + " was not found!"
        )

        return

    clear_output()

    output_queue.put(
        ("Starting " + name + "...", name)
    )

    try:

        active_process = subprocess.Popen(
            [sys.executable, "-u", file_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        active_name = name

        status_label.config(
            text=name + " is running...",
            fg="#55d68b"
        )

        threading.Thread(
            target=read_output,
            args=(active_process, name),
            daemon=True
        ).start()

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
            fg="#ff7777"
        )

    else:

        messagebox.showinfo(
            "Information",
            "No recognition system is running."
        )


# =====================================
# VIEW HISTORY
# =====================================

def view_history():

    create_history_file()

    history_window = tk.Toplevel(root)

    history_window.title("Recognition History")

    history_window.geometry("750x500")

    history_window.configure(bg="#202936")

    heading = tk.Label(
        history_window,
        text="RECOGNITION HISTORY",
        font=("Arial", 18, "bold"),
        bg="#202936",
        fg="white"
    )

    heading.pack(pady=15)

    history_box = scrolledtext.ScrolledText(
        history_window,
        width=85,
        height=23,
        font=("Consolas", 10),
        bg="#111923",
        fg="#55d68b",
        state="normal"
    )

    history_box.pack(
        padx=15,
        pady=10,
        fill="both",
        expand=True
    )

    with open(
        HISTORY_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.reader(file)

        rows = list(reader)

    if len(rows) <= 1:

        history_box.insert(
            tk.END,
            "No recognition history available yet."
        )

    else:

        for row in rows:

            history_box.insert(
                tk.END,
                " | ".join(row) + "\n"
            )

    history_box.config(state="disabled")


# =====================================
# CLEAR HISTORY
# =====================================

def clear_history():

    answer = messagebox.askyesno(
        "Clear History",
        "Are you sure you want to delete all recognition history?"
    )

    if answer:

        with open(
            HISTORY_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date and Time",
                "Recognition Type",
                "Recognized Result",
                "Details"
            ])

        messagebox.showinfo(
            "History",
            "Recognition history cleared successfully."
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
                fg="#55d68b"
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
# MAIN WINDOW
# =====================================

create_history_file()

root = tk.Tk()

root.title("ISL Sign Language Recognition System")

root.geometry("850x760")

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

title.pack(pady=(15, 5))


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
    width=650
)

divider.pack(pady=12)


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

section.pack(pady=5)


# =====================================
# ALPHABET BUTTON
# =====================================

alphabet_button = tk.Button(
    root,
    text="ALPHABET RECOGNITION (A-Z)",
    font=("Arial", 12, "bold"),
    bg="#2878b5",
    fg="white",
    width=32,
    height=2,
    cursor="hand2",
    command=lambda: start_recognition(
        "recognize_v4_voice.py",
        "Alphabet Recognition"
    )
)

alphabet_button.pack(pady=7)


# =====================================
# GREETING BUTTON
# =====================================

greeting_button = tk.Button(
    root,
    text="GREETING RECOGNITION",
    font=("Arial", 12, "bold"),
    bg="#26866b",
    fg="white",
    width=32,
    height=2,
    cursor="hand2",
    command=lambda: start_recognition(
        "recognize_greetings_voice.py",
        "Greeting Recognition"
    )
)

greeting_button.pack(pady=7)


# =====================================
# STOP BUTTON
# =====================================

stop_button = tk.Button(
    root,
    text="STOP RECOGNITION",
    font=("Arial", 11, "bold"),
    bg="#b84a4a",
    fg="white",
    width=25,
    height=2,
    cursor="hand2",
    command=stop_recognition
)

stop_button.pack(pady=7)


# =====================================
# HISTORY BUTTONS
# =====================================

history_frame = tk.Frame(
    root,
    bg="#202936"
)

history_frame.pack(pady=8)


view_button = tk.Button(
    history_frame,
    text="VIEW HISTORY",
    font=("Arial", 10, "bold"),
    bg="#536477",
    fg="white",
    width=17,
    height=2,
    cursor="hand2",
    command=view_history
)

view_button.pack(side="left", padx=8)


clear_history_button = tk.Button(
    history_frame,
    text="CLEAR HISTORY",
    font=("Arial", 10, "bold"),
    bg="#805050",
    fg="white",
    width=17,
    height=2,
    cursor="hand2",
    command=clear_history
)

clear_history_button.pack(side="left", padx=8)


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

status_label.pack(pady=8)


# =====================================
# LIVE OUTPUT
# =====================================

text_title = tk.Label(
    root,
    text="LIVE RECOGNITION OUTPUT",
    font=("Arial", 13, "bold"),
    bg="#202936",
    fg="white"
)

text_title.pack(pady=(8, 5))


output_box = scrolledtext.ScrolledText(
    root,
    width=85,
    height=10,
    font=("Consolas", 10),
    bg="#111923",
    fg="#55d68b",
    insertbackground="white",
    state="disabled"
)

output_box.pack(
    padx=25,
    pady=5
)


# =====================================
# CLEAR LIVE OUTPUT
# =====================================

clear_button = tk.Button(
    root,
    text="CLEAR LIVE TEXT",
    font=("Arial", 10, "bold"),
    bg="#536477",
    fg="white",
    width=18,
    cursor="hand2",
    command=clear_output
)

clear_button.pack(pady=5)


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

footer.pack(side="bottom", pady=10)


# =====================================
# RUN APPLICATION
# =====================================

root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)

root.after(100, update_output)

root.after(1000, check_process)

root.mainloop()