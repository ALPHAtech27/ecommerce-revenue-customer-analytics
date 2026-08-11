"""
run_pipeline.py
----------------
Runs the full analytics pipeline end-to-end, in order:

    1. Generate synthetic data          -> data/raw/
    2. Clean data                       -> data/processed/*_clean.csv
    3. Feature engineering              -> data/processed/*_enriched.csv
    4. RFM segmentation                 -> data/processed/rfm_*.csv
    5. Dashboard dataset generation     -> dashboard/dashboard_data/

Run:
    python scripts/run_pipeline.py
"""

import subprocess
import sys
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("Generating data", "generate_data.py"),
    ("Cleaning data", "clean_data.py"),
    ("Feature engineering", "feature_engineering.py"),
    ("RFM segmentation", "rfm_segmentation.py"),
    ("Dashboard outputs", "generate_dashboard_data.py"),
]


def run_step(step_num, total_steps, label, script_name):
    print(f"\n[{step_num}/{total_steps}] {label}...")
    print("-" * 50)
    script_path = os.path.join(SCRIPT_DIR, script_name)
    result = subprocess.run([sys.executable, script_path], cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"\nERROR: '{script_name}' failed with exit code {result.returncode}.")
        print("Pipeline stopped.")
        sys.exit(result.returncode)


def main():
    start = time.time()

    print("=" * 50)
    print("E-COMMERCE ANALYTICS PIPELINE")
    print("=" * 50)

    total = len(STEPS)
    for i, (label, script_name) in enumerate(STEPS, start=1):
        run_step(i, total, label, script_name)

    elapsed = time.time() - start
    print("\n" + "=" * 50)
    print(f"Pipeline completed successfully in {elapsed:.1f} seconds.")
    print("=" * 50)
    print("\nOutputs available in:")
    print("  data/raw/                    - synthetic source data")
    print("  data/processed/               - cleaned & feature-engineered data")
    print("  dashboard/dashboard_data/     - Power BI-ready CSV extracts")


if __name__ == "__main__":
    main()
