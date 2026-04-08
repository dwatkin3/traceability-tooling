# Traceability Tooling

A Python-based traceability reconciliation tool that cross-references **Test Plans**, **Test Execution results**, and related artefacts to produce a consolidated traceability report.

The tool is designed to be run on a **per-release / per-month** basis using a single, consistent command.

---

## Overview

This repository contains:

- A reusable reconciliation **engine** (`src/v5_engine`)
- Configuration and domain knowledge (patterns, column hints, settings)
- Release-specific inputs (plans, execution spreadsheets, manifests)
- A unified runner script to orchestrate reconciliation runs

The output is an Excel workbook summarising:

- Planned vs executed test coverage
- Missing tests
- Extra (unplanned) tests
- Raw extracted mappings for audit and debugging

---

## Repository Structure

```text
.
├── config/
│   ├── settings.json
│   └── knowledge/
│       ├── patterns.json
│       └── column_hints.json
├── releases/
│   └── 2026.02/
│       ├── manifest.json
│       ├── Test_Plan_2026.02.xlsx
│       ├── Execution_Run_1.xlsx
│       └── Execution_Run_2.xlsx
├── outputs/
│   └── 2026.02/
│       └── Traceability_Reconciliation_2026.02.xlsx
├── src/
│   └── v5_engine/
│       └── run_release.py
├── run_reconcile.py
├── run_release.sh
├── requirements.txt
└── README.md
```

## Requirements

- Python **3.10+**

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Running the Tool

### Unified runner (recommended)

From the repository root:

```bash
python run_reconcile.py YYYY.MM
```

The tool uses openpyxl and pandas for Excel processing.


### Shell wrapper (optional)

A convenience shell wrapper is provided:

```bash
./run_release.sh 2026.02
```



## Running the Tool

### Unified runner (recommended)

From the repository root:

```bash
python run_reconcile.py YYYY.MM
```

This command will:

Configure the Python environment (src/ added to PYTHONPATH)
Suppress non-actionable Excel warnings
Load configuration and knowledge files
Read the release manifest
Run the reconciliation engine
Write outputs to outputs/YYYY.MM/


Shell wrapper (optional)

A convenience shell wrapper is provided:

``
./run_release.sh 2026.02
``

This activates the project virtual environment (if present) and invokes the Python runner.


---

## Release Inputs

Each release/month must have a directory under:

```text
releases/YYYY.MM/
```

At minimum, it must contain:

One test plan file
One or more execution result files

## manifest.json


### Example `manifest.json`

```json
{
  "plan_file": "Test_Plan_2026.02.xlsx",
  "execution_files": [
    "Execution_Run_1.xlsx",
    "Execution_Run_2.xlsx"
  ]
}
```

---

## Outputs

### Excel Report

```text
outputs/YYYY.MM/Traceability_Reconciliation_YYYY.MM.xlsx
```

Debug Outputs

```text

outputs/YYYY.MM/debug/
```

Containing CSV files extracted during reconciliation for audit and diagnostics.

---

## Notes on Excel Warnings

Warnings such as:



## Notes on Excel Warnings

```text
UserWarning: Conditional Formatting extension is not supported```

are emitted by openpyxl and relate only to Excel formatting, not data integrity.
They are safely suppressed by the unified runner.

---

## Development Notes

- Engine logic lives under `src/v5_engine`
- Runner scripts handle CLI arguments, environment setup, and filesystem layout
- Month‑specific runner scripts have been superseded by 

```

run_reconcile.py
```


## Typical Workflow


''text
pip install -r requirements.txtpython run_reconcile.py 2026.02open outputs/2026.02/Traceability_Reconciliation_2026.02.xlsxShow more lines
''

## Maintainer Guidance

The tool is intentionally data-driven.

Most behaviour changes should be handled via manifests or configuration files, not engine code.
