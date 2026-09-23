## 1. BOQ and Cumulative Billing Baseline

Source files:
- data/raw/boq.csv
- data/raw/cumulative_billed_to_RA03.csv
- data/raw/contract_and_policy_terms.md

Rule:
Remaining quantity = Contract quantity - cumulative quantity billed through RA-03.

| BOQ | Contract Qty | Cumulative Billed to RA-03 | Remaining |
|---|---:|---:|---:|
| B01 | 1 LS | 1 LS | 0 LS |
| B02 | 4,000 m | 2,400 m | 1,600 m |
| B03 | 60 nos | 30 nos | 30 nos |
| B04 | 18 km | 9.1 km | 8.9 km |
| B05 | 4,000 m | 3,300 m | 700 m |
| B06 | 60 nos | 18 nos | 42 nos |
| B07 | 1 LS | 0 LS | 1 LS |

Important observations:

- B01 is already fully billed and cannot be billed again.
- B05 has only 700 m remaining under the contract quantity cap.
- B07 has 1 LS remaining, but its milestone completion must be verified from the Primavera schedule before deciding whether it is billable in RA-04.
- These are baseline quantities only. Final RA-04 billable quantities must also consider the September measurement, disputed quantities, QC results, dispatch records, and milestone completion.

## 2. September RA-04 Measurement Audit

Source file:
- data/raw/measurement_sheet_RA04.csv

Contract rules applied:
- PROGRESS items are billed on quantity certified by the client's Engineer-in-Charge.
- Disputed quantity is excluded from billing.
- Cumulative billed quantity cannot exceed the contract quantity.
- Certified quantity above the contract cap is treated as a variation claim, not normal contract-rate billing.

| BOQ | Unit | Measured | Certified | Disputed | RA-03 Billed | Contract Qty | RA-04 Billable | Exception |
|---|---|---:|---:|---:|---:|---:|---:|---|
| B04 | km | 5.2 | 4.9 | 0.3 | 9.1 | 18 | 4.9 | None |
| B05 | m | 950 | 950 | 0 | 3,300 | 4,000 | 700 | 250 m variation claim |
| B06 | nos | 14 | 12 | 2 | 18 | 60 | 12 | 2 disputed |

### Independent calculations

B04:
- 9.1 km previously billed + 4.9 km certified = 14.0 km cumulative.
- Contract quantity = 18 km.
- Therefore 4.9 km is fully billable.

B05:
- 3,300 m previously billed + 950 m certified = 4,250 m.
- Contract quantity = 4,000 m.
- Maximum remaining contract-rate quantity = 4,000 - 3,300 = 700 m.
- Therefore 700 m is billable at the contract rate.
- Remaining 250 m is certified but above the contract quantity cap and must be recorded as a variation claim.

B06:
- 18 nos previously billed + 12 nos certified = 30 nos cumulative.
- Contract quantity = 60 nos.
- Therefore all 12 certified units are billable.
- 2 disputed units are excluded from billing.

B02, B03 and B07 require additional source data before their RA-04 billable quantities can be finalized.

## 3. Production, QC and Schedule Audit

### Production / QC

Source:
- data/raw/production_orders_sep2026.csv

DELIVERY_QC rule:
A quantity is billable only when dispatched to site in the month and passed in-house QC.

B02:
- PO-T-07: 900 m dispatched and QC passed.
- PO-T-08: 600 m dispatched and QC passed.
- PO-T-09: 300 m dispatched but failed QC because zinc coating was below specification.
- QC-passed quantity = 900 + 600 = 1,500 m.
- RA-03 cumulative = 2,400 m.
- Post-RA-04 cumulative = 3,900 m.
- Contract quantity = 4,000 m.
- RA-04 billable = 1,500 m.
- 300 m QC-failed quantity is excluded.

B03:
- PO-P-04: 14 poles dispatched and QC passed.
- PO-P-05: 12 poles dispatched; 2 poles failed QC due to weld defect.
- QC-passed quantity = 14 + (12 - 2) = 24 nos.
- RA-03 cumulative = 30 nos.
- Post-RA-04 cumulative = 54 nos.
- Contract quantity = 60 nos.
- RA-04 billable = 24 nos.
- 2 QC-failed poles are excluded.

### Primavera XER

Source:
- data/raw/SCP2_schedule.xer

Verified:
- Project: SCP2.
- Calendar: 7-Day 8-Hour.
- XER duration and lag fields are expressed in hours.
- WBS nodes: 11.
- Tasks: 13.
- Financial milestones: A1010 and A4010.
- Dependency relationships: 13.
- A1010 Design approval by client: completed 2026-07-05.
- A4010 Commissioning and handover: not started; scheduled for 2026-11-07.

B07 conclusion:
- B07 is a MILESTONE item linked to A4010.
- A4010 is not complete as of the 30 September 2026 reporting date.
- Therefore B07 is not billable in RA-04.
- RA-04 billable quantity for B07 = 0 LS.

## 4. Independent RA-04 Bill Calculation

Bill month:
- September 2026

Bill:
- RA-04

Billable quantities:

| BOQ | Billable Qty | Rate (INR) | Amount (INR) |
|---|---:|---:|---:|
| B02 | 1,500 m | 1,150 | 1,725,000 |
| B03 | 24 nos | 38,500 | 924,000 |
| B04 | 4.9 km | 185,000 | 906,500 |
| B05 | 700 m | 220 | 154,000 |
| B06 | 12 nos | 14,500 | 174,000 |

Gross value:
- ₹3,883,500

GST:
- 18% × ₹3,883,500
- ₹699,030

Retention:
- 5% × ₹3,883,500
- ₹194,175

Mobilisation advance:
- Contract value = ₹13,040,000
- Advance = 8% × ₹13,040,000 = ₹1,043,200
- RA-01 recovery = ₹190,000
- RA-02 recovery = ₹290,000
- RA-03 recovery = ₹238,550
- Total recovered through RA-03 = ₹718,550
- Outstanding before RA-04 = ₹324,650
- RA-04 recovery = ₹324,650

Net payable:
- ₹3,883,500 + ₹699,030 − ₹194,175 − ₹324,650
- ₹4,063,705

Independent expected RA-04 result:
- Gross = ₹3,883,500
- GST = ₹699,030
- Retention = ₹194,175
- Advance recovery = ₹324,650
- Net payable = ₹4,063,705

## 5. Independent Purchase Approval Routing

Source files:
- data/raw/purchase_requests_sep2026.csv
- data/raw/approval_matrix.csv
- data/raw/contract_and_policy_terms.md

Rules:
- Route to the lowest approval level whose limit covers the value, including the stated amount.
- If the required approver is on leave on the request date, route to the next level up.
- Aggregate requests with the same requester, vendor and request date for anti-splitting.
- L4 has no upper limit.

| PR | Value | Expected Level | Expected Approver | Key Rule |
|---|---:|---|---|---|
| PR-101 | ₹42,000 | L1 | Arjun Mehta | Within L1 limit |
| PR-102 | ₹50,000 | L1 | Arjun Mehta | Exactly at L1 limit |
| PR-103 | ₹50,001 | L2 | Neha Kulkarni | Exceeds L1 |
| PR-104 | ₹72,000 | L3 | Vikram Rao | L2 approver on leave |
| PR-105 | ₹45,000 | L3 | Vikram Rao | Aggregated with PR-106 |
| PR-106 | ₹45,000 | L3 | Vikram Rao | Aggregated with PR-105 |
| PR-107 | ₹620,000 | L4 | Suresh Iyer | Exceeds L3 limit |
| PR-108 | ₹80,000 | L3 | Vikram Rao | L2 exact limit but approver on leave |
| PR-109 | ₹80,000 | L2 | Neha Kulkarni | L2 exact limit and approver available |

Anti-splitting:
- PR-105 + PR-106
- Same requester: Ravi Sen
- Same vendor: Bharat Fasteners
- Same date: 2026-09-15
- Aggregate = ₹90,000
- Required level = L3

Leave cases:
- PR-104 on 2026-09-23: Neha Kulkarni unavailable.
- PR-108 on 2026-09-26: Neha Kulkarni unavailable.
- PR-109 on 2026-09-27: Neha Kulkarni available.

## 6. Independent Site Execution Audit

Source:
- data/raw/execution_log_sep2026.csv
- data/raw/measurement_sheet_RA04.csv
- data/raw/SCP2_schedule.xer
- data/raw/contract_and_policy_terms.md

### OFC / B04

Execution-log quantities normalized to km:
- Total site-logged B04 quantity = 8.98 km.
- Measurement sheet measured quantity = 5.20 km.
- Difference = 3.78 km.
- Measurement certified = 4.90 km.
- Measurement disputed = 0.30 km.

The supplied data does not provide a complete explanation for the 3.78 km difference between site logs and measured quantity. The difference must therefore be flagged for operational review rather than silently corrected.

### Capacity exception

EX-908:
- Date: 2026-09-09
- WBS: A3010
- BOQ: B04
- Logged quantity: 4,200 m
- Maximum daily capacity: 400 m/crew/day × 2 crews = 800 m/day.
- Result: FLAGGED as a capacity exception.
- The quantity must not be silently changed to 800 m.

### Invalid WBS

EX-917:
- Date: 2026-09-16
- WBS: A3050
- BOQ: B06
- Quantity: 2 nos.
- A3050 does not exist in the imported SCP2 schedule.
- Result: FLAGGED as invalid WBS.
- The record must not be silently remapped to A3030.

### B05 reconciliation

Execution logs:
- 180 + 150 + 200 + 170 + 250 = 950 m.

Measurement:
- Measured = 950 m.
- Certified = 950 m.
- Disputed = 0 m.

Result:
- Execution and measurement quantities agree at 950 m.
- Only 700 m is billable because the remaining contract quantity after RA-03 is 700 m.
- 250 m is treated as a variation claim.

### B06 reconciliation

Raw execution logs:
- 3 + 2 + 2 + 3 + 2 + 2 = 14 nos.

EX-917 contains an invalid WBS and must be flagged rather than remapped.

Valid WBS-linked execution quantity:
- 3 + 2 + 3 + 2 + 2 = 12 nos.

Measurement:
- Measured = 14 nos.
- Certified = 12 nos.
- Disputed = 2 nos.

The 2 disputed units are excluded from billing.