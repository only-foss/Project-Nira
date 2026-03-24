#!/usr/bin/env python3
"""
=============================================================
Project Nira — Open Hardware Microplastics Detector
File:    nira_reader.py
Purpose: Automatically fetch sensor data from InfluxDB,
         export to CSV, run GNU Octave analysis, and update
         docs/test results in the local repo.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026  only-foss
Repository: https://github.com/only-foss/Project-Nira
Hardware licensed under CERN-OHL-P v2
=============================================================

Usage:
    python nira_reader.py                        # fetch last 1 hour
    python nira_reader.py --start -30m           # last 30 minutes
    python nira_reader.py --start -2h --label clean_water
    python nira_reader.py --start 2026-03-22T11:27:00Z \
                          --stop  2026-03-22T11:36:00Z \
                          --label test-0_cleanWater
    python nira_reader.py --analyse               # fetch + run Octave
    python nira_reader.py --push                  # fetch + analyse + git push

Requirements:
    pip install influxdb-client pandas

Configuration:
    Edit the CONFIG section below OR set environment variables:
        NIRA_INFLUX_URL
        NIRA_INFLUX_TOKEN
        NIRA_INFLUX_ORG
        NIRA_INFLUX_BUCKET
=============================================================
"""

import os
import sys
import argparse
import subprocess
import shutil
from datetime import datetime, timezone
from pathlib import Path

# ── Try importing influxdb_client ──────────────────────────────────────────
try:
    import pandas as pd
    from influxdb_client import InfluxDBClient
except ImportError:
    print("ERROR: Required packages missing. Install with:")
    print("  pip install influxdb-client pandas")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG — edit these OR set environment variables
# ══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    "url":    os.environ.get("NIRA_INFLUX_URL",    "http://your-influxdb-host"),  #change it to your InfluxDB URL
    "token":  os.environ.get("NIRA_INFLUX_TOKEN",  "your_token"),                 #change it to your InfluxDB Token
    "org":    os.environ.get("NIRA_INFLUX_ORG",    "your_org"),                   #change it to your InfluxDB ORG
    "bucket": os.environ.get("NIRA_INFLUX_BUCKET", "your_bucket"),                #change it to your Bucket name
}

# Measurement and device tag as used in firmware
MEASUREMENT = "nira_sensor"
DEVICE_TAG  = "nira_esp32"

# Repo root — assumes this script is in python/ subfolder
REPO_ROOT    = Path(__file__).resolve().parent.parent
TESTS_DATA   = REPO_ROOT / "tests" / "data"
TESTS_ANAL   = REPO_ROOT / "tests" / "analysis"
TESTS_RESULT = REPO_ROOT / "tests" / "results"
# ══════════════════════════════════════════════════════════════════════════════


def fetch(start: str = "-1h", stop: str = "now()", label: str = "nira") -> pd.DataFrame:
    """
    Query InfluxDB for nira_sensor data and return a tidy DataFrame.

    Parameters
    ----------
    start : str
        InfluxDB range start. Examples: '-1h', '-30m', '2026-03-22T11:27:00Z'
    stop  : str
        InfluxDB range stop. Default: 'now()'
    label : str
        Used for the output filename prefix.

    Returns
    -------
    pd.DataFrame with columns: time, ch1_raw, ch4_raw, diff_c1_c4
    """
    print(f"[nira_reader] Connecting to {CONFIG['url']} ...")

    client = InfluxDBClient(
        url=CONFIG["url"],
        token=CONFIG["token"],
        org=CONFIG["org"]
    )

    query = f"""
    from(bucket: "{CONFIG['bucket']}")
      |> range(start: {start}, stop: {stop})
      |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
      |> filter(fn: (r) => r.device == "{DEVICE_TAG}")
      |> filter(fn: (r) => r._field == "ch1_raw"
                        or r._field == "ch4_raw"
                        or r._field == "diff_c1_c4")
      |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> sort(columns: ["_time"])
    """

    print(f"[nira_reader] Querying range: {start} → {stop}")
    df = client.query_api().query_data_frame(query)
    client.close()

    if df.empty:
        print("[nira_reader] WARNING: No data returned for the given range.")
        return df

    # Keep only the columns we need
    cols = [c for c in ["_time", "ch1_raw", "ch4_raw", "diff_c1_c4"] if c in df.columns]
    df = df[cols].copy()
    df.rename(columns={"_time": "time"}, inplace=True)
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"[nira_reader] Fetched {len(df)} samples.")
    return df


def export(df: pd.DataFrame, label: str = "nira") -> Path:
    """
    Save DataFrame to both:
      - tests/data/<label>_<timestamp>.csv  (raw archive)
      - tests/analysis/<mapped_name>.csv    (overwrite for Octave)

    Parameters
    ----------
    df    : pd.DataFrame  data to save
    label : str           filename prefix / test label

    Returns
    -------
    Path to the saved raw CSV
    """
    TESTS_DATA.mkdir(parents=True, exist_ok=True)
    TESTS_ANAL.mkdir(parents=True, exist_ok=True)

    # Timestamped archive copy
    ts       = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    raw_path = TESTS_DATA / f"{label}_{ts}.csv"
    df.to_csv(raw_path, index=False)
    print(f"[nira_reader] Saved raw data → {raw_path}")

    # Map label to Octave analysis CSV name
    label_lower = label.lower()
    if any(k in label_lower for k in ["clean", "water_0", "test_0", "test-0"]):
        anal_name = "clean_water.csv"
    elif any(k in label_lower for k in ["micro", "plastic", "water_1", "test_1", "test-1"]):
        anal_name = "micro_water.csv"
    else:
        anal_name = f"{label}.csv"

    anal_path = TESTS_ANAL / anal_name
    df.to_csv(anal_path, index=False)
    print(f"[nira_reader] Updated analysis CSV → {anal_path}")

    return raw_path


def run_octave() -> bool:
    """
    Run the GNU Octave analysis pipeline.
    Requires: octave installed and nira_analysis.m in tests/analysis/

    Returns
    -------
    bool: True if successful
    """
    octave_bin = shutil.which("octave")
    if not octave_bin:
        print("[nira_reader] WARNING: GNU Octave not found. Skipping analysis.")
        print("  Install with: sudo apt install octave")
        return False

    analysis_script = TESTS_ANAL / "nira_analysis.m"
    if not analysis_script.exists():
        print(f"[nira_reader] WARNING: {analysis_script} not found. Skipping analysis.")
        return False

    TESTS_RESULT.mkdir(parents=True, exist_ok=True)

    print("[nira_reader] Running GNU Octave analysis ...")
    result = subprocess.run(
        [octave_bin, "--no-gui", "nira_analysis.m"],
        cwd=str(TESTS_ANAL),
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("[nira_reader] Octave analysis complete.")
        print(result.stdout)
        return True
    else:
        print("[nira_reader] ERROR: Octave analysis failed.")
        print(result.stderr)
        return False


def git_push(message: str = None) -> bool:
    """
    Stage all changes in tests/ and push to current git branch.

    Parameters
    ----------
    message : str  commit message (auto-generated if None)

    Returns
    -------
    bool: True if push succeeded
    """
    if not shutil.which("git"):
        print("[nira_reader] WARNING: git not found. Skipping push.")
        return False

    ts      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    message = message or f"data: automated nira_reader update {ts}"

    print(f"[nira_reader] Staging and pushing: {message}")

    cmds = [
        ["git", "add", "tests/"],
        ["git", "commit", "-m", message],
        ["git", "push"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        if result.returncode != 0:
            # commit returns 1 if nothing to commit — that's OK
            if "nothing to commit" in result.stdout + result.stderr:
                print("[nira_reader] Nothing new to commit.")
                return True
            print(f"[nira_reader] ERROR running: {' '.join(cmd)}")
            print(result.stderr)
            return False

    print("[nira_reader] Pushed successfully.")
    return True


def print_summary(df: pd.DataFrame) -> None:
    """Print a quick stats summary to console."""
    if df.empty:
        return
    print("\n─── Quick Stats ─────────────────────────────────")
    for col in ["ch1_raw", "ch4_raw", "diff_c1_c4"]:
        if col in df.columns:
            s = df[col].astype(float)
            print(f"  {col:15s}  mean={s.mean():8.2f}  "
                  f"std={s.std():7.2f}  "
                  f"min={s.min():8.2f}  max={s.max():8.2f}")

    diff = df["diff_c1_c4"].astype(float) if "diff_c1_c4" in df.columns else None
    if diff is not None:
        threshold = 92.0
        n_detected = (diff > threshold).sum()
        pct        = 100 * n_detected / len(diff)
        print(f"\n  Detection threshold : {threshold} ADC units")
        print(f"  Samples > threshold : {n_detected}/{len(diff)} ({pct:.1f}%)")
        if pct > 50:
            print("  >> MICROPLASTICS LIKELY PRESENT")
        else:
            print("  >> Water appears CLEAN")
    print("─────────────────────────────────────────────────\n")


# ── CLI ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Project Nira — InfluxDB data fetcher and analysis runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nira_reader.py
  python nira_reader.py --start -2h --label clean_water
  python nira_reader.py --start 2026-03-22T11:27:00Z --stop 2026-03-22T11:36:00Z --label test-0_cleanWater
  python nira_reader.py --analyse
  python nira_reader.py --push
        """
    )
    parser.add_argument("--start",   default="-1h",   help="InfluxDB range start (default: -1h)")
    parser.add_argument("--stop",    default="now()", help="InfluxDB range stop  (default: now())")
    parser.add_argument("--label",   default="nira",  help="Output filename prefix (default: nira)")
    parser.add_argument("--analyse", action="store_true", help="Run GNU Octave analysis after fetch")
    parser.add_argument("--push",    action="store_true", help="Git commit and push after analysis")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print stats only, no files written")

    args = parser.parse_args()

    # Fetch data
    df = fetch(args.start, args.stop, args.label)
    if df.empty:
        sys.exit(1)

    # Print summary always
    print_summary(df)

    if args.dry_run:
        print("[nira_reader] Dry run — no files written.")
        return

    # Export CSVs
    export(df, args.label)

    # Run Octave analysis if requested
    if args.analyse or args.push:
        run_octave()

    # Git push if requested
    if args.push:
        ts  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        git_push(f"data: nira_reader auto-update {ts} [{args.label}]")


if __name__ == "__main__":
    main()
