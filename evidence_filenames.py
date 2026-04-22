from pathlib import Path
import re
from collections import defaultdict

# 🔧 Release you are analysing
release_name = "2026.03"

BASE_DIR = Path(".").resolve()

# 🔥 Correct path
evidence_root = BASE_DIR / "releases" / release_name / "evidence"

print("\n=== ROOT CHECK ===")
print("Path:", evidence_root)
print("Exists:", evidence_root.exists())

if not evidence_root.exists():
    raise SystemExit("❌ Evidence path not found — check release_name or folder structure")

# --- Find release subfolders (RLSE...)
release_dirs = [p for p in evidence_root.iterdir() if p.is_dir()]

print("\n=== RELEASE SUBFOLDERS ===")
for r in release_dirs:
    print("-", r.name)

# --- Regex for test IDs
RE_TEST = re.compile(r"\b[A-Z]{2,}\d+[A-Z]*\b")

test_to_files = defaultdict(list)

print("\n=== SCANNING FILES ===")

for release in release_dirs:
    files = [f for f in release.rglob("*") if f.is_file()]

    print(f"\n-- {release.name} ({len(files)} files) --")

    for f in files[:5]:
        print("  ", f.name)

    for f in files:
        matches = RE_TEST.findall(f.name.upper())
        for m in matches:
            test_to_files[m].append(str(f))

# --- Summary
print("\n=== EVIDENCE BY TEST ID ===")

if not test_to_files:
    print("❌ No test IDs found in filenames")
else:
    for test_id, files in sorted(test_to_files.items()):
        print(f"{test_id} → {len(files)} files")

print(f"\nTOTAL UNIQUE TEST IDs: {len(test_to_files)}")