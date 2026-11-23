
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# =====================================
# 1. FILE PATHS
# =====================================

DATASET_PATH = "dataset/greeting_sequences.csv"
MODEL_PATH = "models/greeting_model.pkl"

os.makedirs("models", exist_ok=True)

print("\n====================================")
print("       GREETING MODEL TRAINING")
print("====================================")

# =====================================
# 2. LOAD DATASET
# =====================================

print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Total samples:", len(df))

# =====================================
# 3. CHECK DATASET
# =====================================

if "Label" not in df.columns:
    raise ValueError("Label column is missing!")

X = df.drop(columns=["Label"])
y = df["Label"]

print("\nGesture counts:")
print(y.value_counts())

print("\nFeature count:", X.shape[1])

if X.shape[1] != 3780:
    raise ValueError("Expected 3780 features.")

X = X.apply(pd.to_numeric, errors="coerce")
X = X.replace([np.inf, -np.inf], np.nan)

if X.isnull().any().any():
    raise ValueError("Missing or invalid values found.")

# =====================================
# 4. SPLIT DATASET
# =====================================

print("\nSplitting dataset...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))

# =====================================
# 5. TRAIN MODEL
# =====================================

print("\nTraining Random Forest...")
print("Please wait...")

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nTraining completed!")

# =====================================
# 6. EVALUATE MODEL
# =====================================

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n====================================")
print("          MODEL RESULTS")
print("====================================")

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

print("\nConfusion Matrix:")

print(confusion_matrix(y_test, predictions))

# =====================================
# 7. SAVE MODEL
# =====================================

model_data = {
    "model": model,
    "sequence_length": 30,
    "features_per_frame": 126,
    "labels": list(model.classes_)
}

joblib.dump(model_data, MODEL_PATH)

print("\nGreeting model saved successfully!")
print("Model location:", MODEL_PATH)

print("\n====================================")
print("          TRAINING FINISHED")
print("====================================")