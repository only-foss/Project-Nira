#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026  only-foss
"""
Project Nira — Dashboard & Live Serial Logger
Provides a full GUI Dashboard (Live Plots, CSV logging, Parameters) 
and a CLI mode for headless operation.
"""

import sys
import csv
import time
import argparse
import threading
import typing
import serial
import serial.tools.list_ports
from collections import deque

def run_cli_mode(port, baud, outfile):
    """Headless CLI mode for serial logging"""
    print(f"--- Nira CLI Mode ---")
    print(f"Connecting to {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"Error opening {port}: {e}")
        return

    print(f"Logging to {outfile} (Press Ctrl+C to stop)")
    with open(outfile, mode='a', newline='') as f:
        writer = csv.writer(f)
        f.seek(0, 2)
        if f.tell() == 0:
            writer.writerow(["time_ms", "CH1_raw", "CH4_raw", "Diff_C1_C4", "Temp_C"])
        
        try:
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if "time_ms" in line or "Sensor ready" in line or "WiFi" in line:
                        print(f"[DEBUG] {line}")
                        continue
                    
                    parts = line.split(',')
                    if len(parts) == 5:
                        writer.writerow(parts)
                        f.flush()
                        print(f"[DATA] ms:{parts[0]} | CH1:{parts[1]} | CH4:{parts[2]} | Diff:{parts[3]} | Temp:{parts[4]}")
        except KeyboardInterrupt:
            print("\nStopped.")
        finally:
            ser.close()

def run_gui_mode(default_port, default_baud, default_out):
    """Full GUI Dashboard using Tkinter and Matplotlib"""
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.animation as animation

    class NiraDashboard(tk.Tk):
        serial_conn: typing.Any
        fig: typing.Any
        ax1: typing.Any
        ax2: typing.Any
        canvas: typing.Any
        port_var: typing.Any
        baud_var: typing.Any
        file_var: typing.Any
        window_var: typing.Any
        port_cb: typing.Any
        connect_btn: typing.Any
        log_btn: typing.Any
        status_lbl: typing.Any
        idx: int
        
        def __init__(self):
            super().__init__()
            self.title("Project Nira — Live Data Dashboard")
            self.geometry("1100x700")
            
            # --- State Variables ---
            self.serial_conn = None
            self.is_logging = False
            self.out_file = default_out
            self.max_pts = 200
            
            # Data Queues
            self.t_data = deque(maxlen=self.max_pts)
            self.ch1_data = deque(maxlen=self.max_pts)
            self.ch4_data = deque(maxlen=self.max_pts)
            self.diff_data = deque(maxlen=self.max_pts)
            
            self.build_ui()
            
            # Start background serial read thread
            self.read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.read_thread.start()
            
            # Matplotlib Animation
            self.anim = animation.FuncAnimation(self.fig, self.update_plot, interval=100, blit=False)

        def build_ui(self):
            # Left Panel: Controls
            control_frame = ttk.Frame(self, width=250, padding=10)
            control_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            # Serial Connection
            ttk.Label(control_frame, text="Connection", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))
            
            ttk.Label(control_frame, text="Port:").pack(anchor=tk.W)
            self.port_var = tk.StringVar(value=default_port)
            self.port_cb = ttk.Combobox(control_frame, textvariable=self.port_var)
            self.port_cb['values'] = [p.device for p in serial.tools.list_ports.comports()]
            self.port_cb.pack(fill=tk.X, pady=2)
            
            ttk.Label(control_frame, text="Baud Rate:").pack(anchor=tk.W, pady=(5,0))
            self.baud_var = tk.StringVar(value=str(default_baud))
            ttk.Combobox(control_frame, textvariable=self.baud_var, values=["9600", "115200", "460800"]).pack(fill=tk.X, pady=2)
            
            self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.toggle_connection)
            self.connect_btn.pack(fill=tk.X, pady=10)
            
            ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
            
            # Logging Configuration
            ttk.Label(control_frame, text="Data Logging", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))
            
            self.file_var = tk.StringVar(value=self.out_file)
            ttk.Label(control_frame, text="CSV File:").pack(anchor=tk.W)
            ttk.Entry(control_frame, textvariable=self.file_var).pack(fill=tk.X, pady=2)
            ttk.Button(control_frame, text="Browse...", command=self.browse_file).pack(fill=tk.X, pady=2)
            
            self.log_btn = ttk.Button(control_frame, text="Start Local Logging", command=self.toggle_logging)
            self.log_btn.pack(fill=tk.X, pady=10)

            ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
            
            # Parameters Control Panel
            ttk.Label(control_frame, text="Parameters", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=(0, 10))
            
            ttk.Label(control_frame, text="Plot Window Size:").pack(anchor=tk.W)
            self.window_var = tk.IntVar(value=self.max_pts)
            ttk.Entry(control_frame, textvariable=self.window_var).pack(fill=tk.X, pady=2)
            ttk.Button(control_frame, text="Apply Parameters", command=self.apply_params).pack(fill=tk.X, pady=10)

            # Signal Threshold status
            self.status_lbl = ttk.Label(control_frame, text="Status: Waiting for data...", foreground="gray")
            self.status_lbl.pack(anchor=tk.W, pady=20)

            # Right Panel: Plots
            plot_frame = ttk.Frame(self)
            plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            self.fig = Figure(figsize=(8, 6), dpi=100)
            self.fig.patch.set_facecolor('#f0f0f0')
            
            self.ax1 = self.fig.add_subplot(211)
            self.ax1.set_title("CH1 (Blue) vs CH4 (Orange) Capacitance")
            self.ax1.set_ylabel("ADC Value")
            
            self.ax2 = self.fig.add_subplot(212)
            self.ax2.set_title("Differential Capacitance (Particle Detection)")
            self.ax2.set_ylabel("Diff (C1 - C4)")
            self.ax2.set_xlabel("Samples")

            self.fig.tight_layout()

            self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def browse_file(self):
            f = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="nira_data.csv")
            if f:
                self.file_var.set(f)

        def toggle_connection(self):
            if self.serial_conn is not None and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
                self.connect_btn.config(text="Connect")
                self.status_lbl.config(text="Status: Disconnected", foreground="red")
            else:
                try:
                    self.serial_conn = serial.Serial(self.port_var.get(), int(self.baud_var.get()), timeout=0.5)
                    self.connect_btn.config(text="Disconnect")
                    self.status_lbl.config(text="Status: Connected", foreground="green")
                except Exception as e:
                    messagebox.showerror("Connection Error", str(e))

        def toggle_logging(self):
            if self.is_logging:
                self.is_logging = False
                self.log_btn.config(text="Start Local Logging")
            else:
                self.out_file = self.file_var.get()
                # Check / auto-create header
                with open(self.out_file, mode='a', newline='') as f:
                    f.seek(0, 2)
                    if f.tell() == 0:
                        csv.writer(f).writerow(["time_ms", "CH1_raw", "CH4_raw", "Diff_C1_C4", "Temp_C"])
                self.is_logging = True
                self.log_btn.config(text="Stop Data Logging")

        def apply_params(self):
            try:
                new_size = int(self.window_var.get())
                self.max_pts = new_size
                # recreate deques
                self.t_data = deque(self.t_data, maxlen=self.max_pts)
                self.ch1_data = deque(self.ch1_data, maxlen=self.max_pts)
                self.ch4_data = deque(self.ch4_data, maxlen=self.max_pts)
                self.diff_data = deque(self.diff_data, maxlen=self.max_pts)
                messagebox.showinfo("Success", "Parameters applied.")
            except ValueError:
                messagebox.showerror("Error", "Invalid Window Size")

        def serial_read_loop(self):
            self.idx = 0
            while True:
                if self.serial_conn is not None and self.serial_conn.is_open:
                    try:
                        while self.serial_conn.in_waiting:
                            line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                            parts = line.split(',')
                            if len(parts) == 5 and parts[0].isdigit():
                                t, c1, c4, df, tmp = parts
                                self.idx += 1
                                self.t_data.append(self.idx)
                                self.ch1_data.append(float(c1))
                                self.ch4_data.append(float(c4))
                                self.diff_data.append(float(df))
                                
                                if self.is_logging:
                                    with open(self.out_file, mode='a', newline='') as f:
                                        csv.writer(f).writerow(parts)
                                        
                                # Simple alert heuristic
                                if float(df) > 90:
                                    self.status_lbl.after(0, lambda: self.status_lbl.config(text="Status: Particle Detected!", foreground="orange"))
                                else:
                                    self.status_lbl.after(0, lambda: self.status_lbl.config(text="Status: Clean", foreground="green"))
                    except Exception as e:
                        print(f"[ERROR] Serial read failed: {e}")
                time.sleep(0.01)

        def update_plot(self, frame):
            if not self.t_data:
                return
            
            self.ax1.clear()
            self.ax2.clear()
            
            self.ax1.set_title("CH1 (Blue) & CH4 (Orange) Capacitance")
            self.ax1.set_ylabel("ADC Value")
            self.ax2.set_title("Differential Capacitance Signal")
            self.ax2.set_ylabel("Diff (C1 - C4)")
            self.ax2.set_xlabel("Samples")

            self.ax1.plot(self.t_data, self.ch1_data, color='blue', alpha=0.7)
            self.ax1.plot(self.t_data, self.ch4_data, color='orange', alpha=0.7)
            
            self.ax2.plot(self.t_data, self.diff_data, color='purple')
            self.ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)

    app = NiraDashboard()
    app.mainloop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Nira — Control Dashboard & Data Logger")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to connect")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200)")
    parser.add_argument("--out", type=str, default="nira_data_local.csv", help="Output file")
    parser.add_argument("--cli", action="store_true", help="Launch in CLI-only mode without GUI")
    
    args = parser.parse_args()

    if args.cli:
        run_cli_mode(args.port, args.baud, args.out)
    else:
        # Check for tkinter / matplotlib locally
        try:
            import tkinter
            import matplotlib
        except ImportError:
            print("ERROR: GUI dependencies missing! Run:")
            print("pip install matplotlib pandas pyserial")
            print("\nFalling back to CLI mode...")
            run_cli_mode(args.port, args.baud, args.out)
            sys.exit(0)
            
        run_gui_mode(args.port, args.baud, args.out)
