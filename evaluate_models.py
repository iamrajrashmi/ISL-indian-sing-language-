import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    ConfusionMatrixDisplay
)


# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODEL_DIR = os.path.join(BASE_DIR, "models")
RESULT_DIR = os.path.join(BASE_DIR, "evaluation_results")

os.makedirs(RESULT_DIR, exist_ok=True)


# ==========================================
# 2. NORMALIZE ALPHABET LANDMARKS
# ==========================================

def normalize_hand(values):

    values = np.array(values, dtype=float)

    if np.all(values == 0):
        return [0.0] * 63

    points = values.reshape(21, 3)

    points = points - points[0]

    distances = np.linalg.norm(points, axis=1)

    scale = np.max(distances)

    if scale > 0:
        points = points / scale

    return points.flatten().tolist()


def normalize_features(row):

    left = normalize_hand(row[:63])

    right = normalize_hand(row[63:126])

    return left + right


# ==========================================
# 3. EVALUATION FUNCTION
# ==========================================

def evaluate_model(name, y_test, predictions, labels):

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="macro",
        zero_division=0
    )

    print("\n===================================")
    print(name)
    print("===================================")

    print(f"Accuracy : {accuracy * 100:.2f}%")
    print(f"Precision: {precision * 100:.2f}%")
    print(f"Recall   : {recall * 100:.2f}%")
    print(f"F1-score : {f1 * 100:.2f}%")

    print("\nClassification Report:")

    report = classification_report(
        y_test,
        predictions,
        labels=labels,
        zero_division=0
    )

    print(report)

    # Save confusion matrix

    display = ConfusionMatrixDisplay.from_predictions(
        y_test,
        predictions,
        labels=labels,
        display_labels=labels,
        xticks_rotation="vertical",
        cmap="Blues",
        colorbar=False
    )

    display.ax_.set_title(name + " Confusion Matrix")

    display.figure.set_size_inches(12, 10)

    plt.tight_layout()

    filename = name.lower().replace(" ", "_")

    image_path = os.path.join(
        RESULT_DIR,
        filename + "_confusion_matrix.png"
    )

    plt.savefig(image_path, dpi=150)

    plt.close()

    print("\nConfusion matrix saved:", image_path)

    return {
        "accuracy": round(float(accuracy), 4),
        "precision_macro": round(float(precision), 4),
        "recall_macro": round(float(recall), 4),
        "f1_macro": round(float(f1), 4),
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=labels,
            output_dict=True,
            zero_division=0
        )
    }


# ==========================================
# 4. ALPHABET MODEL EVALUATION
# ==========================================

def evaluate_alphabet():

    print("\nLoading Alphabet Dataset...")

    dataset_path = os.path.join(
        DATASET_DIR,
        "isl_alphabet_v3.csv"
    )

    data = pd.read_csv(dataset_path)

    feature_columns = (
        [f"L{i}" for i in range(63)] +
        [f"R{i}" for i in range(63)]
    )

    X_raw = data[feature_columns]

    y = data["Label"]

    X = pd.DataFrame(
        [
            normalize_features(row)
            for row in X_raw.values
        ],
        columns=feature_columns
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("Training evaluation-only Alphabet Model...")

    model = RandomForestClassifier(
        n_estimators=700,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    labels = sorted(y.unique())

    results = evaluate_model(
        "Alphabet",
        y_test,
        predictions,
        labels
    )

    return results


# ==========================================
# 5. GREETING MODEL EVALUATION
# ==========================================

def evaluate_greetings():

    print("\nLoading Greeting Dataset...")

    dataset_path = os.path.join(
        DATASET_DIR,
        "greeting_sequences.csv"
    )

    model_path = os.path.join(
        MODEL_DIR,
        "greeting_model.pkl"
    )

    data = pd.read_csv(dataset_path)

    X = data.drop(columns=["Label"])

    y = data["Label"]

    if X.shape[1] != 3780:
        raise ValueError(
            "Greeting feature count is incorrect!"
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("Loading existing Greeting Model...")

    model_data = joblib.load(model_path)

    model = model_data["model"]

    if model.n_features_in_ != X.shape[1]:
        raise ValueError(
            "Greeting model feature mismatch!"
        )

    print("Evaluating existing Greeting Model...")

    predictions = model.predict(X_test)

    labels = sorted(y.unique())

    results = evaluate_model(
        "Greetings",
        y_test,
        predictions,
        labels
    )

    return results


# ==========================================
# 6. MAIN PROGRAM
# ==========================================

def main():

    print("\n")
    print("===================================")
    print(" ISL MODEL PERFORMANCE EVALUATION")
    print("===================================")

    results = {}

    results["alphabet"] = evaluate_alphabet()

    results["greetings"] = evaluate_greetings()

    # Save evaluation metrics

    results_path = os.path.join(
        RESULT_DIR,
        "model_metrics.json"
    )

    with open(results_path, "w") as file:

        json.dump(
            results,
            file,
            indent=4
        )

    print("\n===================================")
    print(" EVALUATION COMPLETED")
    print("===================================")

    print("\nResults saved in:", RESULT_DIR)

    print("\nGenerated files:")

    print("- model_metrics.json")
    print("- alphabet_confusion_matrix.png")
    print("- greetings_confusion_matrix.png")


if __name__ == "__main__":

    main()