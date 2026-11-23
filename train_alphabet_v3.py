import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.utils import shuffle

print("=" * 55)
print("ISL ALPHABET V3 - COMPLETE A TO Z MODEL TRAINING")
print("=" * 55)

# ==========================================
# 1. LOAD DATASET
# ==========================================

DATASET_PATH = "dataset/isl_alphabet_v3.csv"
MODEL_PATH = "models/isl_alphabet_model_v3.pkl"

if not os.path.exists(DATASET_PATH):
    print("ERROR: Dataset not found!")
    raise SystemExit

data = pd.read_csv(DATASET_PATH)

print("\nDataset loaded successfully!")

print("Total samples:", len(data))
print("Total features:", len(data.columns) - 1)
print("Total alphabets:", data["Label"].nunique())

# ==========================================
# 2. CHECK DATASET
# ==========================================

print("\nChecking dataset...")

if data.isnull().values.any():
    print("ERROR: Missing values found!")
    print(data.isnull().sum())
    raise SystemExit

if data.duplicated().sum() > 0:
    print("WARNING: Duplicate rows found:", data.duplicated().sum())

counts = data["Label"].value_counts()

print("\nAlphabet sample counts:")
print(counts.sort_index())

if len(counts) != 26:
    print("ERROR: All 26 alphabets are not available!")
    raise SystemExit

if not all(counts == 100):
    print("ERROR: Some alphabets do not have 100 samples!")
    raise SystemExit

print("\nDataset checks completed!")

# ==========================================
# 3. PREPARE FEATURES
# ==========================================

X = data.drop(columns=["Label"])
y = data["Label"]

X, y = shuffle(X, y, random_state=42)

# ==========================================
# 4. SPLIT DATA
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
# 5. TRAIN MODEL
# ==========================================

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=600,
    max_features="sqrt",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

print("\nTraining completed!")

# ==========================================
# 6. EVALUATE MODEL
# ==========================================

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n" + "=" * 55)
print("MODEL EVALUATION")
print("=" * 55)

print(f"\nTest Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)

# ==========================================
# 7. SAVE NEW MODEL
# ==========================================

os.makedirs("models", exist_ok=True)

joblib.dump(model, MODEL_PATH)

print("\nNew model saved successfully!")
print("Location:", MODEL_PATH)

print("\nOriginal model and dataset were not modified.")

print("\nA-Z training completed!")