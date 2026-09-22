# Delipat Assignment Three — Kaveri Infrasystems

Live implementation for Delipat IT Assignment Three.

## Scope

Build a ClickUp-based project system for Kaveri Infrasystems and implement the four required Python programs against the ClickUp Public API:

1. Schedule importer — Primavera P6 XER → ClickUp WBS, activities, milestones and dependencies.
2. RA-04 bill engine — certified/disputed/QC data → RA-04 bill + client-ready PDF.
3. Approval router — purchase request → correct approver with an explanatory audit comment.
4. Cash-flow forecaster — schedule + remaining quantities + payment terms → October–December 2026 forecast.

A local Ollama model will also classify the 26 execution-log remarks. All calculations are performed by code and independently verified before being compared with AI output.

## Security

The supplied client data pack is confidential. Raw client files are kept locally under `data/raw/` and are intentionally excluded from Git. API tokens and secrets are stored in `.env`, which is also excluded from Git.

Never commit:
- ClickUp API tokens
- `.env`
- confidential client data
- private credentials

## Project structure

```text
.
├── src/
│   ├── ai/
│   ├── clickup/
│   ├── schedule_importer.py
│   ├── ra_bill_engine.py
│   ├── approval_router.py
│   └── cashflow_forecaster.py
├── tests/
├── data/
│   ├── raw/          # confidential input files; not committed
│   └── processed/    # generated local data; not committed
├── docs/             # architecture and design decisions
├── reports/          # build log, expected results, AI/feasibility reports
├── scripts/
├── artifacts/
│   ├── screenshots/
│   ├── bills/
│   └── recording/
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Setup

Python 3.11+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Put the ClickUp personal API token only in `.env`.

## Status

Day 1 — repository and implementation skeleton.

The remaining implementation will be added incrementally with dated commits.
