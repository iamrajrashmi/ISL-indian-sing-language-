import csv
import shutil
import os

file_path = "dataset/isl_data_2hand.csv"
backup_path = "dataset/isl_data_backup.csv"

# Create backup
shutil.copy2(file_path, backup_path)

# Read existing dataset
with open(file_path, "r", newline="") as file:
    rows = list(csv.reader(file))

# Keep header
header = rows[0]

# Remove all samples labelled A
filtered_rows = [
    row for row in rows[1:]
    if row[-1] != "A"
]

# Save cleaned dataset
with open(file_path, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(filtered_rows)

print("Dataset cleaned successfully!")
print("Removed all A samples.")
print("Remaining samples:", len(filtered_rows))
print("Backup created:", backup_path)