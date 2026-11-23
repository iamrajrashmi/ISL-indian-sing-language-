import os
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

print("=" * 55)
print("ISL ALPHABET V4 - NORMALIZED MODEL TRAINING")
print("=" * 55)

DATASET_PATH = "dataset/isl_alphabet_v3.csv"
MODEL_PATH = "models/isl_alphabet_model_v4.pkl"

if not os.path.exists(DATASET_PATH):
    print("ERROR: V3 dataset not found!")
    raise SystemExit

data = pd.read_csv(DATASET_PATH)

print("\nDataset loaded:", len(data))
print("Alphabets:", data["Label"].nunique())

if data.isnull().values.any():
    print("ERROR: Missing values found!")
    raise SystemExit

if data["Label"].nunique() != 26:
    print("ERROR: Dataset must contain all 26 alphabets!")
    raise SystemExit


# ==========================================
# NORMALIZE ONE HAND
# ==========================================

def normalize_hand(values):

    values = np.array(values, dtype=float)

    if np.all(values == 0):
        return [0.0] * 63

    points = values.reshape(21, 3)

    # Wrist becomes the origin
    points = points - points[0]

    # Scale normalization
    distances = np.linalg.norm(points, axis=1)

    scale = np.max(distances)

    if scale > 0:
        points = points / scale

    return points.flatten().tolist()


# ==========================================
# NORMALIZE BOTH HANDS
# ==========================================

def normalize_features(row):

    left = normalize_hand(row[:63])
    right = normalize_hand(row[63:126])

    return left + right


print("\nNormalizing hand coordinates...")

feature_columns = [
    f"L{i}" for i in range(63)
] + [
    f"R{i}" for i in range(63)
]

X_raw = data[feature_columns]

X = pd.DataFrame(
    [normalize_features(row) for row in X_raw.values],
    columns=feature_columns
)

y = data["Label"]

print("Normalization completed!")

# ==========================================
# TRAIN TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# ==========================================
# TRAIN MODEL
# ==========================================

print("\nTraining Random Forest...")

model = RandomForestClassifier(
    n_estimators=700,
    max_features="sqrt",
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nTraining completed!")

# ==========================================
# EVALUATION
# ==========================================

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nTest Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

# ==========================================
# SAVE V4 MODEL
# ==========================================

os.makedirs("models", exist_ok=True)

joblib.dump(model, MODEL_PATH)

print("\nV4 MODEL SAVED SUCCESSFULLY!")
print("Location:", MODEL_PATH)

print("\nV3 dataset and models remain unchanged.")