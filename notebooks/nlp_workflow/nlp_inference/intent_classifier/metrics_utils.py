from typing import Any

import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def evaluate_classification(labels: list[str | int], predictions: list[str | int]) -> dict[str, Any]:
    # Confusion matrix
    conf_matrix = confusion_matrix(labels, predictions)

    # Detailed metrics by class
    class_report = classification_report(labels, predictions, output_dict=True)

    # Overall accuracy
    accuracy = accuracy_score(labels, predictions)

    # Precision by class
    precision = precision_score(labels, predictions, average=None)

    # Recall by class
    recall = recall_score(labels, predictions, average=None)

    # F1-score by class
    f1 = f1_score(labels, predictions, average=None)

    print("Confusion Matrix:")
    print(conf_matrix)
    print("\nClassification Report:")
    print(classification_report(labels, predictions))
    print("\nPrecision by Class:")
    print(precision)
    print("\nRecall by Class:")
    print(recall)
    print("\nF1-Score by Class:")
    print(f1)
    print("\nOverall Accuracy:")
    print(accuracy)

    return {
        "confusion_matrix": conf_matrix,
        "classification_report": class_report,
        "accuracy": accuracy,
        "precision_by_class": precision,
        "recall_by_class": recall,
        "f1_score_by_class": f1,
    }


def plot_metrics(metric_name: str, class_report_dict: dict[str, Any]):
    plt.figure(figsize=(10, 6))
    metrics = {key: value[metric_name] for key, value in class_report_dict.items() if isinstance(value, dict)}
    classes = list(metrics.keys())
    values = list(metrics.values())
    plt.bar(classes, values, color=["blue", "green", "red", "cyan", "magenta"])
    plt.title(f"{metric_name.capitalize()} by Class")
    plt.xlabel("Class")
    plt.ylabel(metric_name.capitalize())
    plt.xticks(rotation=45)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()
