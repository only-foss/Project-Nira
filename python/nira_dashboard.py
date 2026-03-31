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
import os
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
        # type hints
        serial_conn: typing.Any
        fig: typing.Any
        ax1: typing.Any
        ax2: typing.Any
        canvas: typing.Any
        port_var: typing.Any
        baud_var: typing.Any
        file_var: typing.Any
        window_var: typing.Any
        interval_var: typing.Any
        port_cb: typing.Any
        connect_btn: typing.Any
        log_btn: typing.Any
        status_bar: typing.Any
        idx: int
        
        def __init__(self):
            super().__init__()
            self.title("Project Nira — Live Data Dashboard")
            self.geometry("1100x750")
            
            # --- State Variables ---
            self.serial_conn = None
            self.is_logging = False
            self.out_file = default_out
            self.max_pts = 512
            self.update_interval = 100
            
            # Data Queues
            self.t_data = deque(maxlen=self.max_pts)
            self.ch1_data = deque(maxlen=self.max_pts)
            self.ch4_data = deque(maxlen=self.max_pts)
            self.diff_data = deque(maxlen=self.max_pts)
            
            self.build_ui()
            
            # Start background serial read thread
            self.read_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.read_thread.start()
            
            # # Matplotlib Animation
            # self.anim = animation.FuncAnimation(self.fig, self.update_plot, interval=100, blit=False)
            self.anim = animation.FuncAnimation(self.fig, self.update_plot, interval=100, blit=False, cache_frame_data=False)

        def build_ui(self):
            # --- NEW / FIXED: Status Bar at Bottom ---
            self.status_bar = tk.Label(self, text="NOT READY (Stopped / Zeroing)", bg="red", fg="white", font=("Helvetica", 16, "bold"), pady=15)
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

            # Left Panel: Controls
            control_frame = ttk.Frame(self, width=320, padding=10)
            control_frame.pack(side=tk.LEFT, fill=tk.Y)
            control_frame.pack_propagate(False)

            # 1. Connection Frame
            conn_lf = ttk.LabelFrame(control_frame, text="Connection")
            conn_lf.pack(fill=tk.X, pady=5)
            
            ttk.Label(conn_lf, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
            self.port_var = tk.StringVar(value=default_port)
            self.port_cb = ttk.Combobox(conn_lf, textvariable=self.port_var, width=15)
            self.port_cb.grid(row=0, column=1, padx=2, pady=2)
            ttk.Button(conn_lf, text="↻", width=3, command=self.refresh_ports).grid(row=0, column=2, padx=2, pady=2)
            self.refresh_ports()
            
            ttk.Label(conn_lf, text="Baud:").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
            self.baud_var = tk.StringVar(value=str(default_baud))
            ttk.Combobox(conn_lf, textvariable=self.baud_var, values=["9600", "115200", "460800"], width=15).grid(row=1, column=1, padx=2, pady=2)
            
            self.connect_btn = ttk.Button(conn_lf, text="Connect", command=self.toggle_connection)
            self.connect_btn.grid(row=2, column=0, columnspan=3, sticky=tk.EW, padx=2, pady=5)
            
            # 2. Device Controls Frame --- NEW / FIXED: Device control buttons ---
            dev_lf = ttk.LabelFrame(control_frame, text="Device Controls")
            dev_lf.pack(fill=tk.X, pady=5)
            btn_frame = ttk.Frame(dev_lf)
            btn_frame.pack(fill=tk.X, pady=2)
            ttk.Button(btn_frame, text="Start", command=lambda: self.send_command("start\n")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
            ttk.Button(btn_frame, text="Stop", command=lambda: self.send_command("stop\n")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
            ttk.Button(btn_frame, text="Zero", command=lambda: self.send_command("zero\n")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)

            # 3. Logging Frame
            log_lf = ttk.LabelFrame(control_frame, text="Data Logging")
            log_lf.pack(fill=tk.X, pady=5)
            self.file_var = tk.StringVar(value=self.out_file)
            ttk.Entry(log_lf, textvariable=self.file_var).pack(fill=tk.X, padx=2, pady=2)
            ttk.Button(log_lf, text="Browse...", command=self.browse_file).pack(fill=tk.X, padx=2, pady=2)
            self.log_btn = ttk.Button(log_lf, text="Start Local Logging", command=self.toggle_logging)
            self.log_btn.pack(fill=tk.X, padx=2, pady=5)
            
            # 4. Parameters Frame --- NEW / FIXED: Safe Slider Controls ---
            param_lf = ttk.LabelFrame(control_frame, text="Parameters")
            param_lf.pack(fill=tk.X, pady=5)
            
            ttk.Label(param_lf, text="Window Size (100-2000):").pack(anchor=tk.W, padx=2)
            self.window_slider = tk.Scale(param_lf, from_=100, to=2000, orient=tk.HORIZONTAL)
            self.window_slider.set(self.max_pts)
            self.window_slider.pack(fill=tk.X, padx=2)
            
            ttk.Label(param_lf, text="Update Interval ms (50-500):").pack(anchor=tk.W, padx=2)
            self.interval_slider = tk.Scale(param_lf, from_=50, to=500, orient=tk.HORIZONTAL)
            self.interval_slider.set(self.update_interval)
            self.interval_slider.pack(fill=tk.X, padx=2)
            
            ttk.Button(param_lf, text="Apply Parameters", command=self.apply_params).pack(fill=tk.X, padx=2, pady=5)

            # 5. Plot Controls Frame --- NEW / FIXED: More Plot Controls ---
            plot_lf = ttk.LabelFrame(control_frame, text="Plot Controls")
            plot_lf.pack(fill=tk.X, pady=5)
            grid_frame = ttk.Frame(plot_lf)
            grid_frame.pack(fill=tk.X, pady=2)
            ttk.Button(grid_frame, text="Auto Scale Now", command=self.force_autoscale).grid(row=0, column=0, sticky=tk.EW, padx=2, pady=2)
            ttk.Button(grid_frame, text="Clear Plot", command=self.clear_plot).grid(row=0, column=1, sticky=tk.EW, padx=2, pady=2)
            ttk.Button(grid_frame, text="Save Plot PNG", command=self.save_plot).grid(row=1, column=0, sticky=tk.EW, padx=2, pady=2)
            ttk.Button(grid_frame, text="Print Report", command=self.print_report).grid(row=1, column=1, sticky=tk.EW, padx=2, pady=2)
            grid_frame.columnconfigure(0, weight=1)
            grid_frame.columnconfigure(1, weight=1)

            # 6. Analysis Frame --- NEW / FIXED: Post Analysis Button ---
            anal_lf = ttk.LabelFrame(control_frame, text="Analysis")
            anal_lf.pack(fill=tk.X, pady=5)
            ttk.Button(anal_lf, text="📊 Run Post Analysis", command=self.run_post_analysis).pack(fill=tk.X, padx=2, pady=5)

            # Right Panel: Plots
            plot_frame = ttk.Frame(self)
            plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            self.fig = Figure(figsize=(8, 6), dpi=100)
            self.fig.patch.set_facecolor('#f0f0f0')
            
            self.ax1 = self.fig.add_subplot(211)
            self.ax1.set_title("CH1 (Blue) & CH4 (Orange) Capacitance")
            self.ax1.set_ylabel("ADC Value")
            self.line_ch1, = self.ax1.plot([], [], color='blue', alpha=0.7)
            self.line_ch4, = self.ax1.plot([], [], color='orange', alpha=0.7)
            
            self.ax2 = self.fig.add_subplot(212)
            self.ax2.set_title("Differential Capacitance Signal")
            self.ax2.set_ylabel("Diff (C1 - C4)")
            self.ax2.set_xlabel("Samples")
            self.line_diff, = self.ax2.plot([], [], color='purple')
            self.ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)

            self.fig.tight_layout()

            self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        def refresh_ports(self):
            ports = [p.device for p in serial.tools.list_ports.comports()]
            self.port_cb['values'] = ports
            if ports and not self.port_var.get():
                self.port_var.set(ports[0])

        def browse_file(self):
            f = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="nira_data.csv")
            if f:
                self.file_var.set(f)

        def toggle_connection(self):
            if self.serial_conn is not None and self.serial_conn.is_open:
                self.serial_conn.close()
                self.serial_conn = None
                self.connect_btn.config(text="Connect")
                self.update_status("NOT READY (Stopped / Zeroing)", "red")
            else:
                try:
                    self.serial_conn = serial.Serial(self.port_var.get(), int(self.baud_var.get()), timeout=0.5)
                    self.connect_btn.config(text="Disconnect")
                    self.update_status("Waiting for data...", "goldenrod")
                except Exception as e:
                    messagebox.showerror("Connection Error", str(e))

        def send_command(self, cmd: str):
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(cmd.encode('utf-8'))
                except Exception as e:
                    print(f"Failed to send command: {e}")

        def toggle_logging(self):
            if self.is_logging:
                self.is_logging = False
                self.log_btn.config(text="Start Local Logging")
            else:
                self.out_file = self.file_var.get()
                # Check / auto-create header
                try:
                    with open(self.out_file, mode='a', newline='') as f:
                        f.seek(0, 2)
                        if f.tell() == 0:
                            csv.writer(f).writerow(["time_ms", "CH1_raw", "CH4_raw", "Diff_C1_C4", "Temp_C"])
                    self.is_logging = True
                    self.log_btn.config(text="Stop Data Logging")
                except Exception as e:
                    messagebox.showerror("File Error", f"Cannot open file for writing: {e}")

        # --- NEW / FIXED: Safe Parameter updates ---
        def apply_params(self):
            try:
                new_size = int(self.window_var.get() or "256")   # or 512, 100, etc.
                self.max_pts = new_size
                
                i_val = self.interval_slider.get()
                new_interval = int(i_val) if i_val else 100
                self.update_interval = new_interval
                self.anim.event_source.interval = self.update_interval
                
                # recreate deques preserving old data if possible
                self.t_data = deque(self.t_data, maxlen=self.max_pts)
                self.ch1_data = deque(self.ch1_data, maxlen=self.max_pts)
                self.ch4_data = deque(self.ch4_data, maxlen=self.max_pts)
                self.diff_data = deque(self.diff_data, maxlen=self.max_pts)
                messagebox.showinfo("Success", f"Applied: Window={self.max_pts}, Interval={self.update_interval}ms")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid Parameters: {e}")

        def force_autoscale(self):
            try:
                self.ax1.relim()
                self.ax1.autoscale_view(True, True, True)
                self.ax1.margins(y=0.15)
                self.ax2.relim()
                self.ax2.autoscale_view(True, True, True)
                self.ax2.margins(y=0.15)
                self.canvas.draw()
            except Exception as e:
                print(f"Autoscale error: {e}")

        def clear_plot(self):
            self.t_data.clear()
            self.ch1_data.clear()
            self.ch4_data.clear()
            self.diff_data.clear()
            
            # --- NEW / FIXED: Empty line data instead of clearing axes ---
            if hasattr(self, 'line_ch1'):
                self.line_ch1.set_data([], [])
                self.line_ch4.set_data([], [])
                self.line_diff.set_data([], [])
            
            self.canvas.draw()

        def save_plot(self):
            f = filedialog.asksaveasfilename(defaultextension=".png", initialfile="nira_plot.png")
            if f:
                try:
                    self.fig.savefig(f)
                    messagebox.showinfo("Saved", f"Plot saved to {f}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save plot: {e}")

        def print_report(self):
            if not self.diff_data:
                messagebox.showinfo("Report", "No data to generate report.")
                return
            
            diff_list = list(self.diff_data)
            mean_diff = sum(diff_list) / len(diff_list)
            max_diff = max(diff_list)
            detected = sum(1 for d in diff_list if d > 90)
            
            report = f"--- Quick Report ---\n"
            report += f"Total Samples (Window): {len(diff_list)}\n"
            report += f"Mean Diff: {mean_diff:.2f}\n"
            report += f"Max Diff: {max_diff:.2f}\n"
            report += f"Spikes (>90 ADC): {detected}\n\n"
            report += "Likely Particles Present!" if detected > 0 else "Water appears Clean."
            
            messagebox.showinfo("Data Report", report)

        # --- NEW / FIXED: Post Analysis Implementation ---
        def run_post_analysis(self):
            try:
                import pandas as pd
                import sys, os
                
                # --- NEW / FIXED: ensure nira_reader can be imported locally ---
                curr_dir = os.path.dirname(os.path.abspath(__file__))
                if curr_dir not in sys.path:
                    sys.path.insert(0, curr_dir)

                try:
                    # attempt to run existing logic for octace or print summary
                    import nira_reader
                except ImportError:
                    nira_reader = None

                file_path = self.out_file
                if not os.path.exists(file_path):
                    messagebox.showerror("Error", f"No data file found at {file_path}")
                    return

                try:
                    df = pd.read_csv(file_path)
                    
                    if nira_reader and hasattr(nira_reader, 'print_summary'):
                        try:
                            print(f"\n[Post Analysis] Running nira_reader.py logic on {file_path}...")
                            nira_reader.print_summary(df)
                        except Exception as e:
                            print(f"Error calling print_summary: {e}")

                    # Show offline plots in a new window
                    analysis_window = tk.Toplevel(self)
                    analysis_window.title(f"Post Analysis - {file_path}")
                    analysis_window.geometry("900x700")

                    fig = Figure(figsize=(8, 6), dpi=100)
                    ax1 = fig.add_subplot(211)
                    ax1.set_title("Post Analysis - Raw Capacitance")
                    
                    has_data = False
                    
                    # try to detect standard column names even if cases differ
                    ch1_col = next((c for c in df.columns if 'ch1' in c.lower()), None)
                    ch4_col = next((c for c in df.columns if 'ch4' in c.lower()), None)
                    diff_col = next((c for c in df.columns if 'diff' in c.lower()), None)

                    if ch1_col and ch4_col:
                        ax1.plot(df[ch1_col], label=ch1_col)
                        ax1.plot(df[ch4_col], label=ch4_col)
                        ax1.set_ylabel("ADC Value")
                        ax1.legend()
                        has_data = True

                    ax2 = fig.add_subplot(212)
                    ax2.set_title("Post Analysis - Differential Signal")
                    if diff_col:
                        ax2.plot(df[diff_col], color='purple', label=diff_col)
                        ax2.set_ylabel("Diff")
                        ax2.set_xlabel("Samples")
                        ax2.legend()
                        has_data = True

                    if not has_data:
                        ax1.text(0.5, 0.5, 'No recognized columns found in CSV', ha='center', va='center')

                    fig.tight_layout()
                    canvas = FigureCanvasTkAgg(fig, master=analysis_window)
                    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

                except Exception as e:
                    messagebox.showerror("Read Error", f"Failed to read CSV: {e}")

            except Exception as e:
                messagebox.showerror("Analysis Error", f"Could not run analysis: {e}")

        # --- NEW / FIXED: Status update method ---
        def update_status(self, text, bg_color):
            try:
                self.status_bar.config(text=text, bg=bg_color)
            except:
                pass

        def serial_read_loop(self):
            self.idx = 0
            last_data_time = 0
            while True:
                if self.serial_conn is not None and self.serial_conn.is_open:
                    try:
                        while self.serial_conn.in_waiting:
                            line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                            last_data_time = time.time()
                            
                            # check for specific commands from ESP32 confirming status
                            if "streaming_start" in line or "mp_index" in line or (line.startswith('{') and line.endswith('}')):
                                self.after(0, self.update_status, "DATA READY TO LOG ✓", "green")
                                
                            parts = line.split(',')
                            if len(parts) == 5:
                                try:
                                    # Ensure it's valid numerical data
                                    float(parts[1])
                                    
                                    # Valid numeric CSV data streaming
                                    self.after(0, self.update_status, "DATA READY TO LOG ✓", "green")
                                    
                                    t, c1, c4, df_val, tmp = parts
                                    self.idx += 1
                                    self.t_data.append(self.idx)
                                    self.ch1_data.append(float(c1))
                                    self.ch4_data.append(float(c4))
                                    self.diff_data.append(float(df_val))
                                    
                                    if self.is_logging:
                                        with open(self.out_file, mode='a', newline='') as f:
                                            csv.writer(f).writerow(parts)
                                except ValueError:
                                    pass # Headers or non-numeric metadata
                        
                        # --- NEW / FIXED: Timeout updates status if data stops ---
                        if time.time() - last_data_time > 1.5:
                            self.after(0, self.update_status, "Waiting for data...", "goldenrod")
                            
                    except Exception as e:
                        print(f"[ERROR] Serial read failed: {e}")
                        self.after(0, self.update_status, "Waiting for data...", "goldenrod")
                else:
                    self.after(0, self.update_status, "NOT READY (Stopped / Zeroing)", "red")
                time.sleep(0.01)

        def update_plot(self, frame):
            if not self.t_data:
                return
            
            t_list = list(self.t_data)
            self.line_ch1.set_data(t_list, list(self.ch1_data))
            self.line_ch4.set_data(t_list, list(self.ch4_data))
            self.line_diff.set_data(t_list, list(self.diff_data))


            self.ax1.plot(self.t_data, self.ch1_data, color='blue', alpha=0.7)
            self.ax1.plot(self.t_data, self.ch4_data, color='orange', alpha=0.7)
            
            self.ax2.plot(self.t_data, self.diff_data, color='purple')
            self.ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
        # === AUTO SCALING FIX - Add this block ===
        if hasattr(self, 'ax') and len(self.x_data) > 5:   # Only after some data arrives
            self.ax.relim()                  # Re-calculate data limits
            self.ax.autoscale_view(True, True, True)  # Auto scale X and Y
            self.fig.canvas.draw_idle()      # Force redraw
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
