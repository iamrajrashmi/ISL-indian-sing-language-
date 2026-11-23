import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

HISTORY_FILE = os.path.join(BASE_DIR, "recognition_history.csv")

ALPHABET_FILE = "recognize_v4_voice_fullscreen.py"
GREETING_FILE = "recognize_greetings_voice_fullscreen.py"

active_process = None
output_queue = queue.Queue()

# ==========================================
# COLORS
# ==========================================

BG = "#F3F6FC"
NAVY = "#172B4D"
BLUE = "#2864DC"
WHITE = "#FFFFFF"
GREEN = "#15966B"
RED = "#D94C4C"
TEXT = "#26344A"
GREY = "#718096"

# ==========================================
# HISTORY FILE
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
# SAVE HISTORY
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

            parts = line.replace(
                "Detected:", ""
            ).strip().split("|", 1)

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

        update_statistics()


# ==========================================
# STATISTICS
# ==========================================

def update_statistics():

    letters = 0
    words = 0
    greetings = 0

    try:

        create_history_file()

        with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row["Recognition Type"] == "Alphabet":
                    letters += 1

                elif row["Recognition Type"] == "Word":
                    words += 1

                elif row["Recognition Type"] == "Greeting":
                    greetings += 1

        letter_count.set(str(letters))
        word_count.set(str(words))
        greeting_count.set(str(greetings))

    except Exception as error:

        print("Statistics error:", error)


# ==========================================
# READ RECOGNITION OUTPUT
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

        output_box.config(state=tk.NORMAL)

        output_box.insert(tk.END, message + "\n")
        output_box.see(tk.END)

        output_box.config(state=tk.DISABLED)

        try:
            save_history(mode, message)

        except Exception as error:
            print("History error:", error)

    root.after(100, update_output)


# ==========================================
# START RECOGNITION
# ==========================================

def start_recognition(mode):

    global active_process

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
            f"Could not find:\n{file_path}"
        )

        return

    try:

        active_process = subprocess.Popen(
            [sys.executable, "-u", file_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        status_text.set(f"{mode} is running")
        status_label.config(fg=GREEN)

        thread = threading.Thread(
            target=read_output,
            args=(active_process, mode),
            daemon=True
        )

        thread.start()

        output_box.config(state=tk.NORMAL)
        output_box.insert(tk.END, f"\nStarting {mode}...\n")
        output_box.see(tk.END)
        output_box.config(state=tk.DISABLED)

    except Exception as error:

        active_process = None

        messagebox.showerror("Error", str(error))


# ==========================================
# STOP RECOGNITION
# ==========================================

def stop_recognition():

    global active_process

    if active_process is not None:

        if active_process.poll() is None:
            active_process.terminate()

        active_process = None

        status_text.set("Recognition stopped")
        status_label.config(fg=RED)

    else:

        messagebox.showinfo(
            "Information",
            "No recognition is currently running."
        )


# ==========================================
# CLEAR LIVE OUTPUT
# ==========================================

def clear_output():

    output_box.config(state=tk.NORMAL)
    output_box.delete("1.0", tk.END)
    output_box.config(state=tk.DISABLED)


# ==========================================
# VIEW HISTORY
# ==========================================

def view_history():

    create_history_file()

    history_window = tk.Toplevel(root)
    history_window.title("Recognition History")
    history_window.geometry("850x420")
    history_window.configure(bg=BG)

    tk.Label(
        history_window,
        text="RECOGNITION HISTORY",
        font=("Arial", 16, "bold"),
        bg=BG,
        fg=NAVY
    ).pack(pady=12)

    columns = ("Date", "Type", "Result", "Details")

    table = ttk.Treeview(
        history_window,
        columns=columns,
        show="headings"
    )

    table.heading("Date", text="Date and Time")
    table.heading("Type", text="Recognition Type")
    table.heading("Result", text="Recognized Result")
    table.heading("Details", text="Details")

    table.column("Date", width=170)
    table.column("Type", width=140)
    table.column("Result", width=140)
    table.column("Details", width=300)

    table.pack(
        fill=tk.BOTH,
        expand=True,
        padx=15,
        pady=10
    )

    scrollbar = ttk.Scrollbar(
        history_window,
        orient=tk.VERTICAL,
        command=table.yview
    )

    table.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            table.insert(
                "",
                tk.END,
                values=(
                    row["Date and Time"],
                    row["Recognition Type"],
                    row["Recognized Result"],
                    row["Details"]
                )
            )


# ==========================================
# EXPORT HISTORY
# ==========================================

def export_history():

    create_history_file()

    save_path = filedialog.asksaveasfilename(
        title="Export Recognition History",
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile="recognition_history.csv"
    )

    if not save_path:
        return

    try:

        if os.path.abspath(save_path) == os.path.abspath(HISTORY_FILE):

            messagebox.showinfo(
                "Information",
                "This is already the original history file."
            )

            return

        shutil.copy2(HISTORY_FILE, save_path)

        messagebox.showinfo(
            "Success",
            "Recognition history exported successfully!"
        )

    except Exception as error:

        messagebox.showerror("Export Error", str(error))


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

        update_statistics()

        messagebox.showinfo(
            "Success",
            "Recognition history cleared successfully."
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
# BUTTON DESIGN
# ==========================================

def make_button(parent, text, color, command):

    return tk.Button(
        parent,
        text=text,
        font=("Arial", 9, "bold"),
        bg=color,
        fg=WHITE,
        activebackground=color,
        activeforeground=WHITE,
        relief=tk.FLAT,
        bd=0,
        cursor="hand2",
        padx=12,
        pady=8,
        command=command
    )


# ==========================================
# MAIN WINDOW
# ==========================================

root = tk.Tk()

root.title("ISL Recognition Dashboard")

# Compact window for 150% display scaling
root.geometry("1050x650")

root.minsize(850, 600)

root.configure(bg=BG)


# ==========================================
# VARIABLES
# ==========================================

letter_count = tk.StringVar(value="0")
word_count = tk.StringVar(value="0")
greeting_count = tk.StringVar(value="0")

status_text = tk.StringVar(value="System Ready")


# ==========================================
# HEADER
# ==========================================

header = tk.Frame(root, bg=NAVY, height=65)
header.pack(fill=tk.X)
header.pack_propagate(False)

tk.Label(
    header,
    text="ISL RECOGNITION SYSTEM",
    font=("Arial", 18, "bold"),
    bg=NAVY,
    fg=WHITE
).pack(anchor="w", padx=25, pady=(10, 2))

tk.Label(
    header,
    text="Indian Sign Language | Smart Communication Dashboard",
    font=("Arial", 9),
    bg=NAVY,
    fg="#D4DEEF"
).pack(anchor="w", padx=25)


# ==========================================
# WELCOME
# ==========================================

welcome = tk.Frame(root, bg=BG)
welcome.pack(fill=tk.X, padx=25, pady=8)

tk.Label(
    welcome,
    text="Welcome!",
    font=("Arial", 17, "bold"),
    bg=BG,
    fg=NAVY
).pack(anchor="w")

tk.Label(
    welcome,
    text="Recognize signs, form words and communicate easily.",
    font=("Arial", 9),
    bg=BG,
    fg=GREY
).pack(anchor="w")


# ==========================================
# STATISTICS CARDS
# ==========================================

stats_frame = tk.Frame(root, bg=BG)
stats_frame.pack(fill=tk.X, padx=25, pady=5)


def create_stat_card(parent, title, variable, color):

    card = tk.Frame(
        parent,
        bg=WHITE,
        highlightbackground="#E1E7F0",
        highlightthickness=1
    )

    card.pack(
        side=tk.LEFT,
        fill=tk.BOTH,
        expand=True,
        padx=6,
        ipady=4
    )

    tk.Label(
        card,
        text=title,
        font=("Arial", 9, "bold"),
        bg=WHITE,
        fg=GREY
    ).pack(pady=(5, 0))

    tk.Label(
        card,
        textvariable=variable,
        font=("Arial", 20, "bold"),
        bg=WHITE,
        fg=color
    ).pack(pady=(0, 5))


create_stat_card(stats_frame, "ALPHABETS", letter_count, BLUE)
create_stat_card(stats_frame, "WORDS", word_count, GREEN)
create_stat_card(stats_frame, "GREETINGS", greeting_count, "#8B5CC7")


# ==========================================
# RECOGNITION CONTROLS
# ==========================================

recognition_frame = tk.Frame(
    root,
    bg=WHITE,
    highlightbackground="#E1E7F0",
    highlightthickness=1
)

recognition_frame.pack(fill=tk.X, padx=25, pady=8)

tk.Label(
    recognition_frame,
    text="RECOGNITION CONTROL",
    font=("Arial", 11, "bold"),
    bg=WHITE,
    fg=NAVY
).pack(pady=(8, 5))

button_row = tk.Frame(recognition_frame, bg=WHITE)
button_row.pack(pady=3)

make_button(
    button_row,
    "ALPHABET RECOGNITION",
    BLUE,
    lambda: start_recognition("Alphabet Recognition")
).pack(side=tk.LEFT, padx=5)

make_button(
    button_row,
    "GREETING RECOGNITION",
    GREEN,
    lambda: start_recognition("Greeting Recognition")
).pack(side=tk.LEFT, padx=5)

make_button(
    button_row,
    "STOP RECOGNITION",
    RED,
    stop_recognition
).pack(side=tk.LEFT, padx=5)

# ==========================================
# STATUS
# ==========================================

status_frame = tk.Frame(root, bg=BG)
status_frame.pack(fill=tk.X, padx=30, pady=3)

tk.Label(
    status_frame,
    text="SYSTEM STATUS:",
    font=("Arial", 9, "bold"),
    bg=BG,
    fg=TEXT
).pack(side=tk.LEFT)

status_label = tk.Label(
    status_frame,
    textvariable=status_text,
    font=("Arial", 9, "bold"),
    bg=BG,
    fg=GREY
)

status_label.pack(side=tk.LEFT, padx=7)


# ==========================================
# LIVE OUTPUT
# ==========================================

output_frame = tk.Frame(
    root,
    bg=WHITE,
    highlightbackground="#E1E7F0",
    highlightthickness=1
)

output_frame.pack(
    fill=tk.BOTH,
    expand=True,
    padx=25,
    pady=7
)

tk.Label(
    output_frame,
    text="LIVE RECOGNITION OUTPUT",
    font=("Arial", 11, "bold"),
    bg=WHITE,
    fg=NAVY
).pack(anchor="w", padx=12, pady=6)

text_frame = tk.Frame(output_frame)
text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

output_box = tk.Text(
    text_frame,
    height=5,
    font=("Consolas", 9),
    bg="#F8FAFD",
    fg=TEXT,
    relief=tk.FLAT,
    yscrollcommand=scrollbar.set,
    state=tk.DISABLED
)

output_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scrollbar.config(command=output_box.yview)


# ==========================================
# HISTORY MANAGEMENT
# ==========================================

history_frame = tk.Frame(root, bg=BG)
history_frame.pack(fill=tk.X, padx=25, pady=3)

tk.Label(
    history_frame,
    text="HISTORY MANAGEMENT",
    font=("Arial", 11, "bold"),
    bg=BG,
    fg=NAVY
).pack(pady=(2, 6))

history_buttons = tk.Frame(history_frame, bg=BG)
history_buttons.pack(pady=2)

make_button(
    history_buttons,
    "VIEW HISTORY",
    BLUE,
    view_history
).pack(side=tk.LEFT, padx=5)

make_button(
    history_buttons,
    "EXPORT HISTORY",
    GREEN,
    export_history
).pack(side=tk.LEFT, padx=5)

make_button(
    history_buttons,
    "CLEAR HISTORY",
    RED,
    clear_history
).pack(side=tk.LEFT, padx=5)

make_button(
    history_buttons,
    "CLEAR LIVE TEXT",
    NAVY,
    clear_output
).pack(side=tk.LEFT, padx=5)


# ==========================================
# FOOTER
# ==========================================

tk.Label(
    root,
    text="ISL Recognition System | Powered by Python",
    font=("Arial", 8),
    bg=BG,
    fg=GREY
).pack(pady=5)


# ==========================================
# START APPLICATION
# ==========================================

create_history_file()

update_statistics()

root.after(100, update_output)

root.protocol("WM_DELETE_WINDOW", close_application)

root.mainloop()