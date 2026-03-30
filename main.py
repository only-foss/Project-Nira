#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Project Nira — Unified Entry Point

"""
Project Nira Central Launcher.
Provides an overarching entry point for the Project Nira stack.
"""

import sys
import os

def main():
    print("=== Project Nira: Microplastics Detector ===")
    
    # Check if virtual environment is active
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        print("[WARNING] Virtual environment not active. It is recommended to run 'source .venv/bin/activate' first.")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dashboard_path = os.path.join(base_dir, "python", "nira_dashboard.py")
    
    if not os.path.exists(dashboard_path):
        print(f"[ERROR] Could not find {dashboard_path}")
        sys.exit(1)
        
    print(f"Launching Dashboard: {dashboard_path}\n")
    # Use the current active python interpreter
    os.system(f'"{sys.executable}" "{dashboard_path}" ' + " ".join(sys.argv[1:]))

if __name__ == "__main__":
    main()
