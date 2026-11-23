import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# =====================================
# 1. LOAD DATASET
# =====================================

DATASET_PATH = "dataset/isl_data_2hand_v2.csv"

print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully!")
print("Total samples:", len(df))
print("Total columns:", len(df.columns))

# =====================================
# 2. CHECK DATASET
# =====================================

if "Label" not in df.columns:
    raise ValueError("Label column not found!")

if df.isnull().values.any():
    raise ValueError("Dataset contains missing values!")

print("\nAlphabet distribution:")
print(df["Label"].value_counts().sort_index())

# =====================================
# 3. SEPARATE FEATURES AND LABELS
# =====================================

X = df.drop("Label", axis=1)
y = df["Label"]

# Convert features into numeric values
X = X.apply(pd.to_numeric, errors="raise")

print("\nNumber of features:", X.shape[1])
print("Number of alphabets:", y.nunique())

# =====================================
# 4. SPLIT DATASET
# =====================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# =====================================
# 5. CREATE RANDOM FOREST MODEL
# =====================================

print("\nTraining Random Forest model...")

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    n_jobs=-1
)

# =====================================
# 6. TRAIN MODEL
# =====================================

model.fit(X_train, y_train)

print("Model training completed!")

# =====================================
# 7. TEST MODEL
# =====================================

y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("\n================================")
print("MODEL EVALUATION")
print("================================")

print(f"\nModel Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# =====================================
# 8. SAVE TRAINED MODEL
# =====================================

os.makedirs("models", exist_ok=True)

model_data = {
    "model": model,
    "feature_columns": list(X.columns)
}

joblib.dump(
    model_data,
    "models/isl_alphabet_model.pkl"
)

print("\n================================")
print("MODEL SAVED SUCCESSFULLY!")
print("================================")

print("Location: models/isl_alphabet_model.pkl")