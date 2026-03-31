#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Project Nira — Firmware Flash Tool
import os
import sys
import glob
import subprocess

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    clear_screen()
    print("🚀 Project Nira - Firmware Flash Tool")
    print("==================================================")
    print("Default: v1.5 (ESP32-S3)\n")
    
    print("Select Version:")
    print("  1 → v1.5 (ESP32-S3)   ← Default (press Enter to select)")
    print("  2 → v1.0 (ESP32 DOIT V1)")
    
    choice = input("\nEnter choice [1]: ").strip()
    
    version = "1.5"
    if choice == "2":
        version = "1.0"
        
    print(f"\n✅ Selected v{version}")
    
    # Auto-detect ports
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    detected_port = ports[0] if ports else None
    
    if detected_port:
        print(f"📡 Detected Port: {detected_port}\n")
    else:
        print("⚠️  Warning: No /dev/ttyUSB* or /dev/ttyACM* port detected.")
        print("    PlatformIO will attempt auto-detection.\n")
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if version == "1.5":
        env = "esp32-s3-devkitc-1"
        folder = os.path.join(base_dir, "firmware", "v1.5_esp32_fdc1004")
    else:
        env = "esp32dev"
        folder = os.path.join(base_dir, "firmware", "v1.0_esp32_fdc1004")
        
    # Resolve inner PlatformIO root if present (e.g. nested Project-Nira folder)
    if os.path.isdir(os.path.join(folder, "Project-Nira")):
        folder = os.path.join(folder, "Project-Nira")
        
    if not os.path.isdir(folder):
        print(f"❌ Error: Target firmware directory not found:\n   {folder}")
        sys.exit(1)
        
    print("--------------------------------------------------")
    print(f"📁 Target Folder: {os.path.relpath(folder, base_dir)}")
    print(f"⚙️  Target Env:    {env}")
    print("--------------------------------------------------\n")
    
    # Run PlatformIO Clean
    print("🧹 Step 1: Cleaning previous builds...")
    clean_cmd = ["pio", "run", "-t", "clean"]
    try:
        subprocess.run(clean_cmd, cwd=folder, check=True)
    except subprocess.CalledProcessError:
        print("\n❌ Error during clean step. Please ensure PlatformIO ('pio') is installed.")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ Error: 'pio' command not found. Please install PlatformIO Core.")
        sys.exit(1)
        
    # Run PlatformIO Upload and Monitor
    print("\n--------------------------------------------------")
    print("⚡ Step 2: Compiling, Uploading, and Monitoring...")
    print("--------------------------------------------------\n")
    
    upload_cmd = ["pio", "run", "-e", env, "-t", "upload", "-t", "monitor"]
    if detected_port:
        upload_cmd.extend(["--upload-port", detected_port, "--monitor-port", detected_port])
        
    try:
        subprocess.run(upload_cmd, cwd=folder)
    except KeyboardInterrupt:
        print("\n🛑 Monitor stopped by user.")
    except Exception as e:
        print(f"\n❌ Error during upload/monitor: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Exiting tool.")
