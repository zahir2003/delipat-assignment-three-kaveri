# Assignment Three — Feasibility Verdict

## Bucket definitions

- **NATIVE** — Works with standard ClickUp configuration. The required plan is stated.
- **CONFIGURATION** — Achievable through a workaround. The workaround, administration cost, and limitation are stated.
- **CUSTOM BUILD** — Requires code or an external service. The implemented repository evidence or required effort is stated.
- **NOT POSSIBLE** — Cannot be delivered on ClickUp at any plan or price. The client change or acceptance required is stated.

---

## F1 — WBS → execution record → BOQ traceability

**Verdict: CUSTOM BUILD**

**Evidence:** The solution uses the ClickUp WBS hierarchy together with the project-control data model and Python logic to connect WBS activities, execution records and BOQ items.

**Why not native:** ClickUp can represent the hierarchy, but the required project-specific three-level commercial traceability is implemented by the custom control layer.

**Client expectation:** “We can provide the full traceability chain, but it requires the project-control integration we built rather than standard ClickUp configuration alone.”

---

## F2 — Measured, certified and disputed quantities kept separately

**Verdict: CUSTOM BUILD**

**Evidence:** The RA-04 billing engine separately processes measured, certified and disputed quantities and excludes disputed quantities from billable value.

**Why not native:** The rule that disputed quantity must never be billed is contract-specific calculation logic.

**Client expectation:** “The separation and billing protection are implemented in the billing engine; ClickUp is used to expose the resulting controlled record.”

---

## F3 — Monthly progress billing and milestone billing

**Verdict: CUSTOM BUILD**

**Evidence:** The RA-04 billing engine applies the contract billing basis, while the imported P6 schedule provides milestone information. Milestone and progress billing are handled by project-control logic.

**Why not native:** The required billing behavior depends on the project's contract rules and milestone state.

**Client expectation:** “Monthly and milestone billing can be delivered, but the commercial calculation requires the custom billing engine.”

---

## F4 — Automatic Finance notification when billable work or a milestone completes

**Verdict: CUSTOM BUILD**

**Evidence:** The project-control layer determines when work is billable and when a milestone is complete. ClickUp can then be used as the workflow surface for the resulting notification.

**Why not native:** ClickUp does not independently understand the complete contract-specific billability rules used by this project.

**Client expectation:** “Finance notification can be automated after the custom billing logic determines that work is genuinely billable.”

---

## F5 — Purchase approvals routed by value and approver financial limit

**Verdict: CUSTOM BUILD**

**Evidence:** The implemented purchase approval router evaluates request value against the approval matrix and routes each request to the required approval level.

**Why not native:** The assignment requires project-specific financial limits and routing rules.

**Client expectation:** “The approval route is implemented in our control layer because the required financial-limit logic is project-specific.”

---

## F6 — Automatic rerouting when an approver is unavailable

**Verdict: CUSTOM BUILD**

**Evidence:** The approval router checks approver availability and escalates the request when the assigned approver is unavailable.

**Why not native:** The required leave-aware routing behavior is part of the custom approval logic.

**Client expectation:** “We can reroute automatically, but the leave-aware decision requires the custom approval router.”

---

## F7 — Certification blocked without an inspection certificate

**Verdict: CUSTOM BUILD**

**Evidence:** The execution-control rules define the controlled sequence:

`Logged → Under Inspection → Inspection Certificate Received → Certified/Disputed`

Certification is therefore dependent on the inspection-certificate condition.

**Why not native:** ClickUp task statuses alone should not be treated as a strict contractual certification control.

**Client expectation:** “We enforce certification through the control application; ClickUp records the resulting state but is not the sole certification control.”

---

## F8 — WBS-based forecast covering target, executed work, resources and cash

**Verdict: CUSTOM BUILD**

**Evidence:** The solution combines the imported WBS/schedule, progress calculations and cash-flow forecasting logic. The completed cash-flow forecast produces October, November and December 2026 forecast values.

**Why not native:** The requirement combines schedule, execution, resource and financial-control data and therefore needs project-specific integration logic.

**Client expectation:** “The WBS forecast is available through the custom project-control layer combining schedule, execution and cash data.”

---

## F9 — Direct import from Primavera P6 and Microsoft Project

**Verdict: CUSTOM BUILD**

**Evidence:** A Primavera P6 XER importer has been implemented and tested. It imports the SCP2 schedule including 11 WBS nodes, 12 activities/tasks and 13 dependencies, with idempotent ClickUp creation.

**Limitation:** Microsoft Project import is not implemented in the current repository and would require an additional importer or conversion layer.

**Client expectation:** “We have built the P6 import path; Microsoft Project support would require an additional importer or conversion layer.”

---

## F10 — SMS alerts to site engineers

**Verdict: CONFIGURATION**

**Workaround:** Configure ClickUp's SMS integration through Twilio and connect the required ClickUp Automations to the relevant site-engineer events.

**Administration cost:** Twilio account/configuration, phone-number management, integration administration and ongoing third-party SMS service management.

**Limitation:** SMS delivery depends on the external Twilio service and its configuration rather than being an entirely self-contained ClickUp capability.

**Client expectation:** “SMS alerts are achievable through ClickUp's Twilio integration, but they require Twilio configuration and ongoing third-party service administration.”

---

## F11 — All company data stays on the company's own private network

**Verdict: NOT POSSIBLE**

**Evidence:** ClickUp is a SaaS platform hosted on AWS. ClickUp private Spaces provide access/privacy controls but do not turn ClickUp into an on-premises deployment.

**Limitation:** This requirement specifically requires company data to remain on the company's own private network, which is incompatible with ClickUp's hosted SaaS architecture.

**What the client must change or accept:** The client must either accept ClickUp's SaaS hosting model or select a self-hosted/on-premises platform for this requirement.

**Client expectation:** “ClickUp cannot satisfy an on-premises/private-network-only requirement; the client must either accept ClickUp's SaaS hosting model or choose a self-hosted platform.”

---

## F12 — Full data export to Excel at any time, including when leaving the platform

**Verdict: CONFIGURATION**

**Workaround:** Use ClickUp's supported List/Table and task/workspace export capabilities, supplemented by API extraction where a complete exit package requires combining multiple datasets.

**Administration cost:** Export administration, periodic validation of exported datasets, and API/export scripting where required for a complete exit package.

**Limitation:** A complete platform-wide exit package should not be represented as one universal Excel export button; export scope depends on the data type, permissions and available export mechanisms.

**Client expectation:** “Your operational data can be exported, but a complete exit package may require combining ClickUp exports and API data rather than relying on one Excel export.”

---

## F13 — AI agents automatically prepare management reports

**Verdict: CUSTOM BUILD**

**Evidence:** The implemented weekly management report calculates all numerical project-control values deterministically and then uses local Ollama to generate the management narrative. The AI layer is restricted to the supplied controlled report and is instructed not to invent or change numerical facts.

**Why not native:** The assignment's data-control requirement requires company data to remain within a company-controlled/local AI environment rather than being sent to an uncontrolled external AI service.

**Client expectation:** “Automated management reporting is available through our local AI integration, while numerical project controls remain deterministic and protected from AI-generated changes.”

---

## Final F1–F13 Verdict Summary

| Requirement | Verdict |
|---|---|
| F1 | CUSTOM BUILD |
| F2 | CUSTOM BUILD |
| F3 | CUSTOM BUILD |
| F4 | CUSTOM BUILD |
| F5 | CUSTOM BUILD |
| F6 | CUSTOM BUILD |
| F7 | CUSTOM BUILD |
| F8 | CUSTOM BUILD |
| F9 | CUSTOM BUILD |
| F10 | CONFIGURATION |
| F11 | NOT POSSIBLE |
| F12 | CONFIGURATION |
| F13 | CUSTOM BUILD |

### Implementation status

- NATIVE: **0**
- CONFIGURATION: **2**
- CUSTOM BUILD: **10**
- NOT POSSIBLE: **1**

**Important:** F11 is deliberately classified as **NOT POSSIBLE** because the assignment explicitly requires at least one request that cannot be met and asks for the honest client-facing explanation.
