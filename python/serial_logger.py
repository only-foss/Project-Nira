#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026  only-foss — https://github.com/only-foss/Project-Nira
"""
Project Nira — Real-Time Serial Data Logger
Reads ESP32 sensor output over USB and saves to local CSV.
No WiFi, no InfluxDB required.
"""

import csv
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Project Nira - Realtime Serial Data Logger")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port (e.g., /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200)")
    parser.add_argument("--out", type=str, default="nira_local_log.csv", help="Output CSV filename")
    
    args = parser.parse_args()
    
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
        print(f"Connected to {args.port} at {args.baud} baud.")
    except Exception as e:
        print(f"Failed to connect to {args.port}: {e}")
        sys.exit(1)
        
    print(f"Logging data to {args.out}. Press Ctrl+C to stop.")
    
    with open(args.out, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if file is empty
        f.seek(0, 2)
        if f.tell() == 0:
            writer.writerow(["time_ms", "CH1_raw", "CH4_raw", "Diff_C1_C4", "Temp_C"])
            
        try:
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    
                    # Ignore debug strings
                    if "time_ms" in line or "Sensor ready" in line or "WiFi" in line or "InfluxDB" in line:
                        print(f"[DEBUG] {line}")
                        continue
                        
                    parts = line.split(',')
                    if len(parts) == 5:
                        writer.writerow(parts)
                        f.flush()
                        print(f"Logged: {line}")
        except KeyboardInterrupt:
            print("\nLogging stopped by user.")
        finally:
            ser.close()

if __name__ == "__main__":
    main()
