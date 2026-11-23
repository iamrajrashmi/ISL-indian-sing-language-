import pandas as pd
import shutil
import os

path = "dataset/isl_data_2hand_v2.csv"
backup = "dataset/isl_data_backup_before_B_cleanup.csv"

# Check dataset exists
if not os.path.exists(path):
    print("Dataset file not found!")
    raise SystemExit

# Read dataset
df = pd.read_csv(path)

# Identify empty left and right hand landmarks
left_empty = (df.iloc[:, 0:63] == 0).all(axis=1)
right_empty = (df.iloc[:, 63:126] == 0).all(axis=1)

# Find B samples with only one hand
wrong_B = (
    (df["Label"] == "B") &
    (left_empty | right_empty)
)

print("Current samples:")
print(df["Label"].value_counts())

print("\nIncorrect one-hand B samples:", wrong_B.sum())

# Proceed only if exactly one incorrect sample is found
if wrong_B.sum() != 1:
    print("\nExpected exactly one incorrect sample.")
    print("No changes made to your dataset.")
    raise SystemExit

# Create backup
shutil.copy2(path, backup)

# Remove only the incorrect B sample
df = df.loc[~wrong_B].copy()

# Save updated dataset
df.to_csv(path, index=False)

print("\nIncorrect B sample removed!")
print("\nUpdated samples:")
print(df["Label"].value_counts())

print("\nBackup saved at:", backup)