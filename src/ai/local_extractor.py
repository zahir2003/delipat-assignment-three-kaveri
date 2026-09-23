"""Local Ollama classifier for execution-log delay remarks.

This module:
1. Reads the September 2026 execution log.
2. Sends each remark only to a locally running Ollama model.
3. Classifies delay category and explicitly stated delay hours.
4. Saves model predictions separately from human ground truth.
5. Calculates field-level accuracy against the independent hand labels.

No execution-log data is sent to an external AI service.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]

EXECUTION_LOG = PROJECT_ROOT / "data" / "raw" / "execution_log_sep2026.csv"
GROUND_TRUTH = PROJECT_ROOT / "data" / "processed" / "execution_remarks_labels.csv"
PREDICTIONS = PROJECT_ROOT / "data" / "processed" / "local_ollama_predictions.csv"
ACCURACY_REPORT = PROJECT_ROOT / "data" / "processed" / "local_ollama_accuracy.json"

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

ALLOWED_CATEGORIES = {
    "weather",
    "material",
    "equipment",
    "authority",
    "traffic",
    "labour",
    "inspection",
    "other",
    "none",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def build_prompt(remark: str) -> str:
    """Build a strict classification prompt for the local model."""
    return f"""
You are classifying one construction execution-log remark.

Classify ONLY the information explicitly present in the remark.

Allowed delay_category values:
weather, material, equipment, authority, traffic, labour, inspection, other, none

Rules:
1. Use "none" when the remark does not describe a delay.
2. Use "not stated" for delay_hours when a numeric number of hours is NOT explicitly stated.
3. Do NOT convert phrases such as "half day", "pura din", "aadha din", or similar
   into an estimated number of hours.
4. Do NOT infer a duration from the quantity, shift length, calendar, or context.
5. If the remark explicitly says "2 hours", return 2.
6. Return delay_hours as either a number or the exact string "not stated".
7. Return ONLY valid JSON. No markdown and no explanation.

JSON schema:
{{
  "delay_category": "one allowed category",
  "delay_hours": "number or not stated"
}}

Remark:
{remark}
""".strip()


def call_ollama(remark: str) -> dict[str, Any]:
    """Send one remark to the local Ollama HTTP API."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": build_prompt(remark),
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
        },
    }

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    data = response.json()
    raw_output = data.get("response", "").strip()

    if not raw_output:
        raise ValueError("Ollama returned an empty response")

    result = json.loads(raw_output)

    category = str(result.get("delay_category", "")).strip().lower()
    hours = result.get("delay_hours", "not stated")

    if category not in ALLOWED_CATEGORIES:
        raise ValueError(
            f"Invalid delay_category from Ollama: {category!r}"
        )

    if isinstance(hours, str):
        hours = hours.strip().lower()

        if hours != "not stated":
            try:
                hours = float(hours)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid delay_hours from Ollama: {hours!r}"
                ) from exc

    elif isinstance(hours, (int, float)):
        hours = float(hours)

    else:
        raise ValueError(
            f"Invalid delay_hours type from Ollama: {type(hours).__name__}"
        )

    return {
        "delay_category": category,
        "delay_hours": hours,
    }


def normalize_hours(value: Any) -> str:
    """Normalize numeric/string hour values for comparison."""
    if isinstance(value, str):
        value = value.strip().lower()

        if value == "not stated":
            return "not stated"

        try:
            number = float(value)
        except ValueError:
            return value
    else:
        number = float(value)

    if number.is_integer():
        return str(int(number))

    return str(number)


def calculate_accuracy(
    predictions: list[dict[str, str]],
    ground_truth: list[dict[str, str]],
) -> dict[str, Any]:
    """Calculate independent field-level accuracy."""
    truth_by_id = {row["log_id"]: row for row in ground_truth}

    category_correct = 0
    hours_correct = 0
    total = 0

    for prediction in predictions:
        log_id = prediction["log_id"]

        if log_id not in truth_by_id:
            raise ValueError(
                f"Prediction {log_id} has no matching ground-truth label"
            )

        truth = truth_by_id[log_id]

        predicted_category = prediction["delay_category"].strip().lower()
        true_category = truth["delay_category"].strip().lower()

        predicted_hours = normalize_hours(prediction["delay_hours"])
        true_hours = normalize_hours(truth["delay_hours"])

        if predicted_category == true_category:
            category_correct += 1

        if predicted_hours == true_hours:
            hours_correct += 1

        total += 1

    if total == 0:
        raise ValueError("No predictions available for accuracy calculation")

    return {
        "model": OLLAMA_MODEL,
        "ollama_url": OLLAMA_URL,
        "total_records": total,
        "delay_category": {
            "correct": category_correct,
            "total": total,
            "accuracy": round(category_correct / total, 4),
        },
        "delay_hours": {
            "correct": hours_correct,
            "total": total,
            "accuracy": round(hours_correct / total, 4),
        },
    }


def main() -> None:
    """Run local extraction and independent accuracy evaluation."""
    if not EXECUTION_LOG.exists():
        raise FileNotFoundError(f"Execution log not found: {EXECUTION_LOG}")

    if not GROUND_TRUTH.exists():
        raise FileNotFoundError(f"Ground truth not found: {GROUND_TRUTH}")

    execution_rows = load_csv(EXECUTION_LOG)
    ground_truth = load_csv(GROUND_TRUTH)

    if len(execution_rows) != 26:
        raise ValueError(
            f"Expected 26 execution remarks, found {len(execution_rows)}"
        )

    if len(ground_truth) != 26:
        raise ValueError(
            f"Expected 26 ground-truth labels, found {len(ground_truth)}"
        )

    print(f"Using local Ollama: {OLLAMA_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Classifying {len(execution_rows)} execution remarks...")
    print()

    predictions: list[dict[str, str]] = []

    for index, row in enumerate(execution_rows, start=1):
        result = call_ollama(row["remarks"])

        prediction = {
            "log_id": row["log_id"],
            "delay_category": result["delay_category"],
            "delay_hours": normalize_hours(result["delay_hours"]),
        }

        predictions.append(prediction)

        print(
            f"[{index:02d}/26] {row['log_id']} -> "
            f"{prediction['delay_category']}, "
            f"{prediction['delay_hours']}"
        )

    PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)

    with PREDICTIONS.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "log_id",
                "delay_category",
                "delay_hours",
            ],
        )
        writer.writeheader()
        writer.writerows(predictions)

    accuracy = calculate_accuracy(predictions, ground_truth)

    with ACCURACY_REPORT.open("w", encoding="utf-8") as file:
        json.dump(accuracy, file, indent=2)

    print()
    print("=== Local Ollama Accuracy ===")
    print(
        f"Delay category: "
        f"{accuracy['delay_category']['correct']}/"
        f"{accuracy['delay_category']['total']} "
        f"({accuracy['delay_category']['accuracy']:.2%})"
    )
    print(
        f"Delay hours: "
        f"{accuracy['delay_hours']['correct']}/"
        f"{accuracy['delay_hours']['total']} "
        f"({accuracy['delay_hours']['accuracy']:.2%})"
    )
    print()
    print(f"Predictions saved to: {PREDICTIONS}")
    print(f"Accuracy report saved to: {ACCURACY_REPORT}")


if __name__ == "__main__":
    main()