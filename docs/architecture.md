# Architecture

Implemented flow:

`Primavera XER → Schedule Importer → ClickUp WBS/Activities → Execution Records → BOQ → Measurement/Certification → RA-04 → Cash Forecast`

Supporting flows:

- `Purchase Request → Approval Router → Approver + Audit Evidence`
- `Execution Remark → Local Ollama → Delay Category + Delay Hours → ClickUp`
- `ClickUp data + deterministic calculations → verified management report narrative`

The implementation separates deterministic project-control calculations from AI-generated narrative/extraction. Financial and billing calculations are performed by Python code, while local Ollama is used for execution-log language extraction and the management-report narrative.

Design decisions, rejected alternatives, and reasons are documented where applicable in the repository and feasibility assessment.