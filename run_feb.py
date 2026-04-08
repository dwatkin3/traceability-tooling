#!/usr/bin/env python3
from pathlib import Path
from v5_engine.run_release import run_release

def main():
    ROOT=Path(__file__).resolve().parent
    RELEASE_DIR=ROOT/'releases'/'2026.02'
    result=run_release(
        root_dir=RELEASE_DIR,
        manifest_path=RELEASE_DIR/'manifest.json',
        settings_path=ROOT/'config'/'settings.json',
        patterns_path=ROOT/'config'/'knowledge'/'patterns.json',
        hints_path=ROOT/'config'/'knowledge'/'column_hints.json'
    )
    print('February reconciliation complete.')
    print('ABS OUTPUT:', result['output'])

if __name__=='__main__': main()
