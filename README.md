# Delipat Assignment Three — Kaveri Infrasystems

Live implementation for Delipat IT Assignment Three.

This repository contains the implemented ClickUp-based project-control system and the four required Python programs for Smart Corridor Package 2 (SCP2).

## Scope

The implementation covers:

1. **Schedule importer** — Primavera P6 XER → ClickUp WBS, activities, milestones and dependencies.
2. **RA-04 bill engine** — certified/disputed/QC data → RA-04 bill calculation and client-ready PDF.
3. **Approval router** — purchase request → correct approval level, including unavailability and anti-splitting rules.
4. **Cash-flow forecaster** — schedule + remaining quantities + payment terms → October–December 2026 forecast.

Supporting AI functionality includes:

- Local Ollama extraction of delay category and delay hours from 26 execution-log remarks.
- Local Ollama generation of a management-report narrative.
- ClickUp AI verification against independently calculated project values.

All financial and project-control calculations are performed deterministically by Python code.

## Key Results

### Automated Tests

**22/22 tests passed.**

### Local Ollama Evaluation

- Delay-category accuracy: **24/26 (92.31%)**
- Delay-hours accuracy: **26/26 (100%)**
- Model execution is local through Ollama.

### ClickUp AI Verification

Six required project questions were tested against ClickUp task-level AI.

**6/6 correct (100%)**

The questions covered:

- WBS and activity/milestone counts
- Contract value
- RA-04 financial values
- Cash-flow forecast
- B02 RA-04 quantity and rate
- B04 measured/certified/disputed quantities

### RA-04

RA-04 for September 2026 was calculated from the controlled project data and includes:

- Gross value
- GST
- Retention
- Mobilisation advance recovery
- Net payable
- Disputed quantities excluded
- Contract quantity cap and variation handling

### Cash-flow Forecast

Forecast window:

**October–December 2026**

The forecast uses the contract payment terms and deterministic calculations.

## Data Handling

The supplied client data pack is confidential.

- Raw client files remain local under `data/raw/` and are excluded from Git.
- Generated local data under `data/processed/` is excluded from Git.
- API tokens and secrets are stored only in `.env`.
- `.env` and confidential data are excluded through `.gitignore`.
- Local Ollama is used for execution-log language extraction.
- Financial calculations are performed by deterministic Python code.
- ClickUp AI results are independently verified against calculated project values.

Never commit:

- ClickUp API tokens
- `.env`
- confidential client data
- private credentials

## Project Structure

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
├── docs/
│   ├── architecture.md
│   ├── data-handling.md
│   ├── build_log.md
│   └── expected_results.md
├── reports/
├── screenshots/      # assignment evidence screenshots
├── artifacts/
├── .env.example
├── .gitignore
├── BUILD_LOG.md
├── FEASIBILITY.md
├── pyproject.toml
├── requirements.txt
└── README.md