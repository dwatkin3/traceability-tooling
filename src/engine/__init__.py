"""V5 Traceability Reconciler package (clean, final).
- Plan parser (DOCX tables) → Story → Tests (atomic IDs)
- Execution parser (XLSX multi-sheet) → rows (sheet,row,story,test,file)
- Reconcile → Missing/Extra + per-story coverage
- Writer → always writes Summary + debug CSVs
"""
