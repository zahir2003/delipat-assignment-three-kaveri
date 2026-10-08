"""
This file creates a short weekly management narrative from the prepared project report.
We need it to make key updates easier to read while keeping narrative generation local.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3",
)


"""
Builds constrained instructions so the local model summarizes the report without inventing unsupported facts.
"""


def build_prompt(report_text: str) -> str:
    """Build a prompt for management narrative only."""

    return f"""
You are writing a concise weekly management narrative for a
construction project.

The report below contains numbers already calculated by deterministic
project-control software.

Your job is ONLY to summarize the facts and identify management
attention points already present in the supplied report.

Strict rules:
1. Do NOT calculate any new numbers.
2. Do NOT change, reinterpret, or estimate any number.
3. Do NOT invent project facts, causes, dates, quantities, costs,
   risks, or recommendations.
4. Use only information explicitly present in the supplied report.
5. Keep the narrative concise and professional.
6. Do not provide financial calculations.
7. Do not output markdown tables.
8. Return ONLY valid JSON.

Return exactly this structure:

{{
  "summary": "2-4 sentence factual management summary",
  "attention_points": [
    "factual point from the supplied report"
  ]
}}

Controlled weekly report:
{report_text}
""".strip()


"""
Requests a narrative from local Ollama and returns structured text for the weekly-report workflow.
"""


def generate_narrative(report_text: str) -> dict[str, Any]:
    """Generate narrative using local Ollama only."""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": build_prompt(report_text),
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

    summary = result.get("summary")
    attention_points = result.get("attention_points")

    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Ollama returned an invalid summary")

    if not isinstance(attention_points, list):
        raise ValueError("Ollama returned invalid attention_points")

    cleaned_points = []

    for point in attention_points:
        if not isinstance(point, str):
            raise ValueError("Ollama returned a non-string attention point")

        point = point.strip()

        if point:
            cleaned_points.append(point)

    return {
        "summary": summary.strip(),
        "attention_points": cleaned_points,
    }


"""
Runs a local smoke test so Ollama connectivity and narrative generation can be checked directly.
"""


def main() -> None:
    """Simple local-Ollama smoke test."""

    sample_report = """
KAVERI INFRASYSTEMS — WEEKLY MANAGEMENT REPORT

Reporting date: 2026-09-30
Project: SCP2

Schedule validation: PASS
Activity progress: 71.08%
Completed activities: 3/12
Completed milestones: 1/2

RA-04 gross value: INR 3,883,500.00
RA-04 net payable: INR 4,063,705.00
Disputed value excluded: INR 84,500.00

October 2026 cash inflow: INR 2,385,500.00
November 2026 cash inflow: INR 4,063,705.00
December 2026 cash inflow: INR 6,107,085.00

Key exception:
B05: 250 m certified above contract quantity; recorded as variation.
""".strip()

    result = generate_narrative(sample_report)

    print("Local Ollama weekly narrative")
    print("============================")
    print()
    print("Summary:")
    print(result["summary"])
    print()
    print("Attention points:")

    for point in result["attention_points"]:
        print(f"- {point}")


if __name__ == "__main__":
    main()
