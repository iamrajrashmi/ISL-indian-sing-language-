import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

print("=" * 50)
print("ISL ALPHABET MODEL - COMPLETE A TO Z TRAINING")
print("=" * 50)

# Load dataset
DATASET_PATH = "dataset/isl_data_2hand_v2.csv"

data = pd.read_csv(DATASET_PATH)

print("\nDataset loaded successfully!")
print("Total samples:", len(data))

# Separate features and labels
X = data.drop(columns=["Label"])
y = data["Label"]

# Check dataset
if y.nunique() != 26:
    raise ValueError("Dataset must contain all 26 alphabets!")

if X.isnull().sum().sum() > 0:
    raise ValueError("Dataset contains missing values!")

print("Total features:", X.shape[1])
print("Total alphabets:", y.nunique())

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# Create improved model
print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=500,
    max_features="sqrt",
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nTraining completed!")

# Evaluate model
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n" + "=" * 50)
print("MODEL EVALUATION")
print("=" * 50)

print(f"\nTest Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

# Save new model separately
os.makedirs("models", exist_ok=True)

MODEL_PATH = "models/isl_alphabet_model_v2.pkl"

joblib.dump(model, MODEL_PATH)

print("\nNew model saved successfully!")
print("Location:", MODEL_PATH)

print("\nOriginal alphabet model remains unchanged.")
print("Training process completed!")