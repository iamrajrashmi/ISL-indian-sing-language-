import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import threading
import queue
import os
import sys
import csv
import shutil
from datetime import datetime

# ==========================================
# SETTINGS
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

HISTORY_FILE = os.path.join(
    BASE_DIR, "recognition_history.csv"
)

ALPHABET_FILE = "recognize_v4_voice.py"
GREETING_FILE = "recognize_greetings_voice.py"

active_process = None
active_mode = None

output_queue = queue.Queue()


# ==========================================
# CREATE HISTORY FILE
# ==========================================

def create_history_file():

    if not os.path.exists(HISTORY_FILE):

        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date and Time",
                "Recognition Type",
                "Recognized Result",
                "Details"
            ])


# ==========================================
# SAVE RECOGNITION HISTORY
# ==========================================

def save_history(mode, line):

    line = line.strip()

    recognition_type = None
    result = ""
    details = ""

    if mode == "Alphabet Recognition":

        if line.startswith("Added:"):

            recognition_type = "Alphabet"
            result = line.replace("Added:", "").strip()

        elif line.startswith("Word saved:"):

            recognition_type = "Word"
            result = line.replace("Word saved:", "").strip()

    elif mode == "Greeting Recognition":

        if line.startswith("Detected:"):

            recognition_type = "Greeting"

            parts = line.replace("Detected:", "").strip().split("|", 1)

            result = parts[0].strip()

            if len(parts) > 1:
                details = parts[1].strip()

    if recognition_type:

        with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow([
                datetime.now().strftime("%d-%m-%Y %I:%M:%S %p"),
                recognition_type,
                result,
                details
            ])


# ==========================================
# READ OUTPUT FROM RECOGNITION PROGRAM
# ==========================================

def read_output(process, mode):

    try:

        for line in process.stdout:

            output_queue.put((line.rstrip(), mode))

    except Exception as error:

        output_queue.put((f"Output error: {error}", mode))

    finally:

        output_queue.put(("Recognition process finished.", mode))


# ==========================================
# UPDATE LIVE OUTPUT
# ==========================================

def update_output():

    while not output_queue.empty():

        message, mode = output_queue.get()

        output_box.insert(tk.END, message + "\n")
        output_box.see(tk.END)

        try:
            save_history(mode, message)

        except Exception as error:

            output_box.insert(
                tk.END,
                f"History save error: {error}\n"
            )

    root.after(100, update_output)


# ==========================================
# CLEAR LIVE OUTPUT
# ==========================================

def clear_output():

    output_box.delete("1.0", tk.END)


# ==========================================
# START RECOGNITION
# ==========================================

def start_recognition(mode):

    global active_process, active_mode

    if active_process is not None and active_process.poll() is None:

        messagebox.showwarning(
            "Recognition Running",
            "Please stop the current recognition first."
        )

        return

    if mode == "Alphabet Recognition":

        file_path = os.path.join(BASE_DIR, ALPHABET_FILE)

    else:

        file_path = os.path.join(BASE_DIR, GREETING_FILE)

    if not os.path.exists(file_path):

        messagebox.showerror(
            "File Not Found",
            f"Could not find {file_path}"
        )

        return

    active_mode = mode

    output_box.insert(
        tk.END,
        f"\nStarting {mode}...\n"
    )

    output_box.see(tk.END)

    try:

        active_process = subprocess.Popen(
            [sys.executable, "-u", file_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        thread = threading.Thread(
            target=read_output,
            args=(active_process, mode),
            daemon=True
        )

        thread.start()

    except Exception as error:

        active_process = None

        messagebox.showerror(
            "Error",
            str(error)
        )


# ==========================================
# STOP RECOGNITION
# ==========================================

def stop_recognition():

    global active_process

    if active_process is not None:

        if active_process.poll() is None:

            active_process.terminate()

            output_box.insert(
                tk.END,
                "\nStopping recognition...\n"
            )

            output_box.see(tk.END)

        active_process = None

    else:

        messagebox.showinfo(
            "Information",
            "No recognition is currently running."
        )


# ==========================================
# VIEW HISTORY
# ==========================================

def view_history():

    create_history_file()

    history_window = tk.Toplevel(root)

    history_window.title("Recognition History")
    history_window.geometry("750x450")

    heading = tk.Label(
        history_window,
        text="RECOGNITION HISTORY",
        font=("Arial", 16, "bold")
    )

    heading.pack(pady=10)

    history_text = tk.Text(
        history_window,
        font=("Consolas", 10),
        wrap=tk.NONE
    )

    history_text.pack(
        fill=tk.BOTH,
        expand=True,
        padx=10,
        pady=10
    )

    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:

        reader = csv.reader(file)

        for row in reader:

            history_text.insert(
                tk.END,
                " | ".join(row) + "\n"
            )

    history_text.config(state=tk.DISABLED)


# ==========================================
# EXPORT HISTORY
# ==========================================

def export_history():

    create_history_file()

    save_path = filedialog.asksaveasfilename(
        title="Export Recognition History",
        defaultextension=".csv",
        filetypes=[
            ("CSV Files", "*.csv"),
            ("All Files", "*.*")
        ],
        initialfile="recognition_history.csv"
    )

    if not save_path:

        return

    try:

        if os.path.abspath(save_path) == os.path.abspath(HISTORY_FILE):

            messagebox.showinfo(
                "Export History",
                "This is already the original history file."
            )

            return

        shutil.copy2(HISTORY_FILE, save_path)

        messagebox.showinfo(
            "Export Successful",
            f"History exported successfully!\n\nSaved at:\n{save_path}"
        )

    except Exception as error:

        messagebox.showerror(
            "Export Error",
            str(error)
        )


# ==========================================
# CLEAR HISTORY
# ==========================================

def clear_history():

    answer = messagebox.askyesno(
        "Clear History",
        "Are you sure you want to delete all recognition history?"
    )

    if answer:

        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Date and Time",
                "Recognition Type",
                "Recognized Result",
                "Details"
            ])

        messagebox.showinfo(
            "History Cleared",
            "Recognition history has been cleared."
        )


# ==========================================
# CLOSE APPLICATION
# ==========================================

def close_application():

    global active_process

    if active_process is not None:

        if active_process.poll() is None:

            active_process.terminate()

    root.destroy()


# ==========================================
# GUI DESIGN
# ==========================================

root = tk.Tk()

root.title("ISL Sign Language Recognition System")
root.geometry("850x760")

root.configure(bg="#eeeeee")


title = tk.Label(
    root,
    text="ISL SIGN LANGUAGE RECOGNITION SYSTEM",
    font=("Arial", 18, "bold"),
    bg="#eeeeee",
    fg="#222222"
)

title.pack(pady=20)


# ==========================================
# RECOGNITION BUTTONS
# ==========================================

button_frame = tk.Frame(root, bg="#eeeeee")
button_frame.pack(pady=10)


alphabet_button = tk.Button(
    button_frame,
    text="ALPHABET RECOGNITION",
    width=25,
    height=2,
    command=lambda: start_recognition("Alphabet Recognition")
)

alphabet_button.grid(row=0, column=0, padx=10, pady=10)


greeting_button = tk.Button(
    button_frame,
    text="GREETING RECOGNITION",
    width=25,
    height=2,
    command=lambda: start_recognition("Greeting Recognition")
)

greeting_button.grid(row=0, column=1, padx=10, pady=10)


stop_button = tk.Button(
    button_frame,
    text="STOP RECOGNITION",
    width=25,
    height=2,
    command=stop_recognition
)

stop_button.grid(row=1, column=0, columnspan=2, pady=10)


# ==========================================
# LIVE OUTPUT HEADING
# ==========================================

output_heading = tk.Label(
    root,
    text="LIVE RECOGNITION OUTPUT",
    font=("Arial", 13, "bold"),
    bg="#eeeeee"
)

output_heading.pack(pady=10)


# ==========================================
# LIVE OUTPUT PANEL
# ==========================================

output_frame = tk.Frame(root)

output_frame.pack(
    fill=tk.BOTH,
    expand=True,
    padx=25,
    pady=10
)


scrollbar = tk.Scrollbar(output_frame)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


output_box = tk.Text(
    output_frame,
    height=15,
    font=("Consolas", 10),
    yscrollcommand=scrollbar.set
)

output_box.pack(
    side=tk.LEFT,
    fill=tk.BOTH,
    expand=True
)

scrollbar.config(command=output_box.yview)


# ==========================================
# HISTORY BUTTONS
# ==========================================

history_frame = tk.Frame(root, bg="#eeeeee")

history_frame.pack(pady=15)


view_button = tk.Button(
    history_frame,
    text="VIEW HISTORY",
    width=18,
    height=2,
    command=view_history
)

view_button.grid(row=0, column=0, padx=5)


export_button = tk.Button(
    history_frame,
    text="EXPORT HISTORY",
    width=18,
    height=2,
    command=export_history
)

export_button.grid(row=0, column=1, padx=5)


clear_history_button = tk.Button(
    history_frame,
    text="CLEAR HISTORY",
    width=18,
    height=2,
    command=clear_history
)

clear_history_button.grid(row=0, column=2, padx=5)


clear_output_button = tk.Button(
    history_frame,
    text="CLEAR LIVE TEXT",
    width=18,
    height=2,
    command=clear_output
)

clear_output_button.grid(row=1, column=1, pady=10)


# ==========================================
# START APPLICATION
# ==========================================

create_history_file()

root.after(100, update_output)

root.protocol(
    "WM_DELETE_WINDOW",
    close_application
)

root.mainloop()