# Traceability Reconciler (v5)

## Overview

The Traceability Reconciler is a deterministic reconciliation engine
designed to validate alignment between:

-   Test Plans (intended coverage)
-   Test Execution results (actual coverage)
-   Release scope (story-level expectations)

It produces structured, audit-ready outputs to support Test Assurance,
governance reviews, and delivery confidence.

This tool is specifically designed for environments where traceability
is critical and must withstand external scrutiny (e.g. CAB, audit,
supplier handover).

------------------------------------------------------------------------

## Why This Exists

In real delivery environments, inconsistencies frequently occur:

-   Tests planned but never executed\
-   Tests executed under the wrong story\
-   Duplicate execution across multiple stories\
-   Lack of evidence for passed tests

Manual reconciliation is slow, subjective, and error-prone.

This tool provides:

-   Objective reconciliation logic\
-   Repeatable and deterministic outputs\
-   Clear classification of issues\
-   A consistent audit trail

------------------------------------------------------------------------

## Core Concepts

Understanding these definitions is critical for interpreting outputs:

### Missing Test

A test that exists in the plan but is not executed anywhere.

### Misaligned Test

A test that was executed, but under a different story than planned.

### Extra Test

A test that was executed but does not exist in the plan for that story.

### Duplicate Test

A test executed under more than one story.

### Passed with Evidence

A test marked as passed with valid supporting evidence.

------------------------------------------------------------------------

## How to Run

From the repository root:

``` bash
python run_reconcile.py YYYY.MM
```

Outputs will be generated in:

    outputs/YYYY.MM/

------------------------------------------------------------------------

## Inputs

Each release folder should contain:

    releases/YYYY.MM/

With:

-   One test plan file\
-   One or more execution files\
-   A manifest.json describing inputs

Example:

``` json
{
  "plan_file": "Test_Plan.xlsx",
  "execution_files": [
    "Execution_1.xlsx",
    "Execution_2.xlsx"
  ]
}
```

------------------------------------------------------------------------

## Outputs Explained

The tool produces a multi-sheet Excel workbook.

### 1. Summary

Purpose: - High-level story status overview

Contains: - Traceability status (missing / misaligned) - Execution
status (pass/fail/evidence) - Counts of planned vs executed tests

Interpretation: - 🔴 Tests missing → coverage gap exists\
- 🟡 Tests present (not linked) → executed elsewhere\
- 🟢 Tests present → fully aligned

------------------------------------------------------------------------

### 2. Traceability Gaps

Purpose: - Detailed breakdown of coverage issues

Contains: - Missing tests\
- Misaligned tests\
- Extra tests\
- Coverage counts

Interpretation: - Focus here for root cause analysis\
- Misaligned tests indicate execution errors\
- Missing tests indicate coverage gaps

------------------------------------------------------------------------

### 3. Execution Detail

Purpose: - Test-level audit trail

Contains: - Each planned test\
- Where it was executed\
- Alignment status\
- Execution result

Interpretation: - "Aligned = NO" → execution occurred under wrong story\
- "NOT EXECUTED" → test missing entirely

------------------------------------------------------------------------

### 4. Supporting Sheets

-   Story_To_Test_Map → plan structure\
-   Execution_Attachments → raw execution data\
-   Plan_Raw / Exec_Raw → audit extraction

These support traceability back to source data.

------------------------------------------------------------------------

## Regression Testing

The tool includes regression validation to ensure stability.

Run:

``` bash
python tests/regression/run_regression.py
```

This will:

1.  Run the engine\
2.  Compare outputs to a baseline\
3.  Fail if differences exist

This guarantees:

-   No unintended behavioural drift\
-   Safe refactoring\
-   Reproducible results

------------------------------------------------------------------------

## Design Principles

-   Normalise once at ingestion\
-   Deterministic outputs\
-   Separation of concerns (parser → engine → writer)\
-   Data-driven behaviour\
-   Audit-first design

------------------------------------------------------------------------

## Assumptions & Known Behaviours

### Assumptions

-   Input files follow expected formats\
-   Story identifiers follow pattern (e.g. STRYxxxx)\
-   Test IDs are unique identifiers\
-   Execution files contain consistent status values

------------------------------------------------------------------------

### Known Behaviours

-   Misaligned tests are treated as coverage gaps\
-   Duplicate tests are reported but not automatically resolved\
-   Evidence is treated as a binary flag (yes/no)\
-   Output ordering may differ but data remains consistent

------------------------------------------------------------------------

## Limitations

-   Relies on consistent naming conventions\
-   Does not infer missing relationships automatically\
-   Does not validate business logic correctness of tests

------------------------------------------------------------------------

## Maintainer Guidance

-   Always run regression tests before committing\
-   Do not introduce implicit data transformations\
-   Prefer configuration over logic changes\
-   Treat output structure as contract

------------------------------------------------------------------------

## Summary

This tool is designed to be:

-   Deterministic\
-   Transparent\
-   Auditable\
-   Safe to evolve

It should be treated as a controlled component within the delivery
process, not a disposable script.
