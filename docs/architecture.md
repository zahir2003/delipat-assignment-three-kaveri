# Architecture

Planned flow:

`Primavera XER → Schedule Importer → ClickUp WBS/Activities → Execution Records → BOQ → Measurement/Certification → RA-04 → Cash Forecast`

Supporting flows:

- `Purchase Request → Approval Router → Approver + Audit Comment`
- `Execution Remark → Local Ollama → Delay Category + Delay Hours → ClickUp`
- `ClickUp data + deterministic calculations → verified management report narrative`

Design decisions will be recorded with rejected alternatives and reasons as required by the assignment.
