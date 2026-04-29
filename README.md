# Traceability Reconciler (v5)

A deterministic traceability reconciliation engine that validates
alignment between:

-   Test Plans\
-   Test Execution results\
-   Release scope (story-level coverage)

It produces audit-ready outputs to support Test Assurance, delivery
confidence, and release governance.

------------------------------------------------------------------------

## Purpose

In complex delivery environments, discrepancies frequently arise
between:

-   Planned test coverage\
-   Executed tests\
-   Evidence of execution

This tool provides an objective, repeatable mechanism to:

-   Identify missing, misaligned, and extra tests\
-   Validate execution evidence\
-   Produce a consistent traceability view per release

------------------------------------------------------------------------

## Key Concepts

-   Missing Test: Planned but not executed anywhere\
-   Misaligned Test: Executed, but under the wrong story\
-   Extra Test: Executed but not part of the plan\
-   Duplicate Test: Same test executed under multiple stories\
-   Passed with Evidence: Passed test with supporting evidence present

------------------------------------------------------------------------

## Running the Tool

``` bash
python run_reconcile.py YYYY.MM
```

Outputs are written to:

outputs/YYYY.MM/

------------------------------------------------------------------------

## Regression Testing

``` bash
python tests/regression/run_regression.py
```

Ensures deterministic outputs and prevents unintended changes.

------------------------------------------------------------------------

## Design Principles

-   Normalise once at ingestion\
-   Deterministic outputs\
-   Separation of concerns\
-   Data-driven configuration

------------------------------------------------------------------------

## Maintainer Guidance

-   Validate all logic changes with regression tests\
-   Prefer configuration over code changes\
-   Keep behaviour stable and auditable
