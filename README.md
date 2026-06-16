# Traceability Reconciler (v5)

![CI](https://github.com/dwatkin3/traceability-tooling/actions/workflows/validate.yaml/badge.svg)

## Overview

The Traceability Reconciler validates alignment between:

- Release scope
- Test specifications / plans
- Test execution results
- Evidence artefacts

It produces an audit-ready workbook designed for governance reviews, CABs, supplier assurance, release sign-off and traceability audits.

---

# 🚀 Quick Start

## macOS / Linux

```bash
git clone <repository-url>
cd traceability-tooling

chmod +x *.sh

./create_regression_evidence.sh
./bootstrap.sh 2026.04
./validate.sh 2026.04
```

## Windows (Git Bash)

```bash
git clone <repository-url>
cd traceability-tooling

./create_regression_evidence.sh
./bootstrap.sh 2026.04
./validate.sh 2026.04
```

## Common Commands

| Action | Command |
|----------|----------|
| Validate release | `./validate.sh 2026.04` |
| Clean rebuild + validate | `./bootstrap.sh 2026.04` |
| Update regression baseline | `./validate.sh 2026.04 --update-baseline` |
| Archive previous output | `./validate.sh 2026.04 --archive` |

---

# 📥 Inputs

Each release folder contains:

```text
releases/YYYY.MM/
```

With:

- One or more specification documents (.docx)
- One or more execution workbooks (.xlsx)
- A manifest.json describing the inputs

Example:

```json
{
  "plan_files": [
    "Spec_A.docx",
    "Spec_B.docx"
  ],
  "execution_files": [
    "Execution_1.xlsx",
    "Execution_2.xlsx"
  ]
}
```

Supported scenarios:

- Single specification releases
- Multi-specification releases
- Multiple execution workbooks
- RLSE identifiers
- Descriptive release names

---

# 📤 Outputs Explained (How to Read the Results)

The generated workbook contains several views of the same reconciliation data.

## 1. Dashboard

Purpose:

Provides an executive summary of release health.

Key metrics:

- Planned stories
- Executed stories
- Coverage %
- Failed tests
- Missing tests
- Misaligned tests

Use when:

- Presenting to CAB
- Release governance reviews
- Quick health assessment

---

## 2. Summary

Purpose:

Primary story-level reconciliation view.

Typical statuses:

### Traceability

🟢 Tests present  
🟡 Tests present (not linked)  
🔴 Tests missing

### Execution Status

🟢 Passed with evidence  
🟢 Passed  
🔴 Failed tests present  
🔴 No execution tests

Interpretation examples:

🟢 Traceability + 🟢 Exec Status
→ Fully reconciled.

🟡 Traceability + 🟢 Exec Status
→ Tests executed but linked incorrectly.

🔴 Traceability + 🟢 Exec Status
→ Execution looks healthy but planned coverage is incomplete.

🔴 Traceability + 🔴 Exec Status
→ Significant release risk.

---

## 3. Traceability Gaps

Purpose:

Diagnostic view explaining WHY reconciliation failed.

Highlights:

- Missing tests
- Extra tests
- Misaligned tests
- Duplicate tests
- Missing evidence

This is usually the first sheet used during investigation.

---

## 4. Execution Detail

Purpose:

Complete test-by-test audit trail.

Contains:

- Planned story
- Execution story
- Test ID
- Status
- Evidence flag
- Alignment result
- Workbook source
- Worksheet source

Useful for:

- Audit
- Supplier challenge
- Root-cause analysis

---

## 5. Traceability Matrix

Purpose:

Canonical flattened dataset.

Contains one row per planned/executed test relationship.

Designed for:

- Power BI
- Filtering
- Audit exports
- Downstream tooling
- Machine-readable analysis

Includes:

- Missing tests
- Misaligned tests
- Execution-only tests
- Execution-only stories
- Evidence status

---

## 6. Supporting Sheets

Used for parser transparency and troubleshooting.

Examples:

- plan_raw
- exec_raw
- parser diagnostics

These sheets help explain how the engine interpreted source documents.

---

# 🧪 Regression Testing

Regression testing is built into the solution.

Validation compares:

```text
outputs/YYYY.MM/Traceability_Reconciliation_YYYY.MM.xlsx
vs
tests/regression/baseline/Traceability_Reconciliation_YYYY.MM.xlsx
```

Update the baseline intentionally:

```bash
./validate.sh 2026.04 --update-baseline
```

Regression currently covers:

- Multiple specifications
- Multiple execution workbooks
- Descriptive release names
- Missing tests
- Misaligned tests
- Duplicate tests
- Missing evidence
- Execution-only stories
- Hyphenated test IDs
- Range expansion
- Dashboard metrics
- Traceability Matrix

---

# 🔄 Architecture

## End-to-End Flow

```text
Plans (.docx)
        \
         -> Parse -> Reconcile -> Generate Workbook
        /
Executions (.xlsx)
```

## Design Principles

- Deterministic outputs
- Audit-first design
- Transparent reconciliation
- Minimal hidden behaviour
- Reproducible regression testing

---

# Recent Enhancements

## Multi-Spec Releases

Supports multiple specification documents within a single release.

## Expanded Test ID Support

Examples:

- AU12
- IS70A
- TP-CREW-01
- TP-OPT-01

Range support:

- AU01-AU05
- IS70A-D

## Dashboard

Executive release-level metrics.

## Traceability Matrix

Canonical flattened reconciliation dataset.

## Recursive Evidence Discovery

Evidence can be organised beneath release-specific subfolders.

---

# Utilities

## bootstrap.sh

Creates a clean environment and validates a release.

## validate.sh

Runs reconciliation and regression checking.

## create_regression_evidence.sh

Generates synthetic regression evidence files.

Safe to run repeatedly.

## generate_manifest.sh

Builds release manifests.

## reset_venv.sh

Rebuilds Python environment.

---

# Maintainer Guidance

Before committing:

1. Run validation.
2. Review regression results.
3. Understand differences before updating baselines.
4. Keep workbook outputs backward compatible where possible.

The workbook structure should be treated as a contract for auditors, governance users and downstream tooling.
