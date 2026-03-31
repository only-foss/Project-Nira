#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
nira_gui.py — Project Nira Desktop GUI
=======================================
Real-time dashboard + control interface + one-click printable report
for the ESP32-S3 Microplastics Detector.

Dependencies (all FOSS):
    pip install pyserial matplotlib numpy tkinter-tooltip

Usage:
    python nira_gui.py [--port /dev/ttyUSB0] [--baud 115200]

License: MIT
Project: https://github.com/only-foss/Project-Nira
"""

import argparse
import csv
import json
import os
import queue
import sys
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import AutoMinorLocator
import numpy as np
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ─── Constants ────────────────────────────────────────────────────────────────
APP_NAME      = "Project Nira — Microplastics Monitor"
APP_VERSION   = "v1.1.0"
DEFAULT_BAUD  = 115200
MAX_POINTS    = 600          # rolling window (samples)
CHANNEL_NAMES = ["CH0", "CH1", "CH2", "CH3"]
CHANNEL_COLS  = ["#00b4d8", "#90e0ef", "#0077b6", "#48cae4"]
MP_COL        = "#f77f00"
DANGER_THRESH = 0.10         # mp_index threshold for alert (pF RMS)
LOG_DIR       = Path("nira_logs")

# ─── Colour Palette ───────────────────────────────────────────────────────────
DARK_BG   = "#0d1b2a"
PANEL_BG  = "#1b2a3b"
ACCENT    = "#00b4d8"
TEXT_FG   = "#e0f0ff"
WARN_FG   = "#f77f00"
OK_FG     = "#52b788"
BORDER    = "#2a3f55"

# ─── Serial Reader Thread ─────────────────────────────────────────────────────

class SerialReader(threading.Thread):
    """
    Background thread that reads newline-delimited JSON from the ESP32
    and pushes parsed dicts into a thread-safe queue.
    """

    def __init__(self, port: str, baud: int, data_q: queue.Queue):
        super().__init__(daemon=True)
        self.port    = port
        self.baud    = baud
        self.data_q  = data_q
        self._stop   = threading.Event()
        self.ser     = None
        self.connected = False

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            self.connected = True
            return True
        except serial.SerialException as e:
            self.data_q.put({"_error": str(e)})
            return False

    def stop(self):
        self._stop.set()
        if self.ser and self.ser.is_open:
            self.ser.close()

    def send(self, cmd: str):
        """Send a command string to the device."""
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\n").encode())

    def run(self):
        if not self.connect():
            return
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = self.ser.read(128)
                if not chunk:
                    continue
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line.decode("utf-8", errors="replace"))
                        self.data_q.put(obj)
                    except json.JSONDecodeError:
                        # pass through raw string for status display
                        self.data_q.put({"_raw": line.decode("utf-8", errors="replace")})
            except serial.SerialException as e:
                self.data_q.put({"_error": f"Serial lost: {e}"})
                break
            except Exception:
                pass

# ─── Data Store ───────────────────────────────────────────────────────────────

class DataStore:
    """Rolling buffer for sensor data; thread-safe append from reader."""

    def __init__(self, maxlen=MAX_POINTS):
        self.ts        = deque(maxlen=maxlen)   # relative time, seconds
        self.ch        = [deque(maxlen=maxlen) for _ in range(4)]
        self.delta     = [deque(maxlen=maxlen) for _ in range(4)]
        self.mp_index  = deque(maxlen=maxlen)
        self.temp      = deque(maxlen=maxlen)
        self.bat_mv    = deque(maxlen=maxlen)
        self._t0       = None
        self._lock     = threading.Lock()
        self.records   = []   # full history for CSV export

    def push(self, obj: dict):
        if "mp_index" not in obj:
            return
        with self._lock:
            ts_raw = obj.get("ts", 0) / 1000.0  # ms → s
            if self._t0 is None:
                self._t0 = ts_raw
            t = ts_raw - self._t0

            self.ts.append(t)
            for i in range(4):
                self.ch[i].append(obj.get(f"ch{i}", 0.0))
                self.delta[i].append(obj.get(f"d{i}", 0.0))
            self.mp_index.append(obj.get("mp_index", 0.0))
            self.temp.append(obj.get("temp", 0.0))
            self.bat_mv.append(obj.get("bat_mv", 0))
            self.records.append({
                "datetime": datetime.now().isoformat(timespec="seconds"),
                "ts_s": round(t, 3),
                "n": obj.get("n", 0),
                **{f"ch{i}_pF": round(obj.get(f"ch{i}", 0.0), 5) for i in range(4)},
                **{f"d{i}_pF":  round(obj.get(f"d{i}",  0.0), 5) for i in range(4)},
                "mp_index": round(obj.get("mp_index", 0.0), 6),
                "temp_c": obj.get("temp", 0.0),
                "bat_mv": obj.get("bat_mv", 0),
            })

    def snapshot(self):
        """Return numpy arrays of current rolling data (thread-safe copy)."""
        with self._lock:
            ts       = np.array(self.ts)
            ch       = [np.array(c) for c in self.ch]
            delta    = [np.array(d) for d in self.delta]
            mp       = np.array(self.mp_index)
            temp     = np.array(self.temp)
            bat      = np.array(self.bat_mv)
        return ts, ch, delta, mp, temp, bat

    def export_csv(self, path: Path):
        with self._lock:
            rows = list(self.records)
        if not rows:
            return False
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return True

# ─── Main GUI Application ─────────────────────────────────────────────────────

class NiraApp:
    def __init__(self, root: tk.Tk, args):
        self.root    = root
        self.args    = args
        self.reader  = None
        self.data_q  = queue.Queue()
        self.store   = DataStore()
        self._running = True

        LOG_DIR.mkdir(exist_ok=True)

        self._build_ui()
        self._schedule_poll()

        # Auto-connect if port specified
        if args.port:
            self.port_var.set(args.port)
            self._connect()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.title(f"{APP_NAME}  {APP_VERSION}")
        self.root.configure(bg=DARK_BG)
        self.root.minsize(1100, 700)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=PANEL_BG, height=56)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        tk.Label(top, text="◈  PROJECT NIRA", font=("Courier", 16, "bold"),
                 bg=PANEL_BG, fg=ACCENT).pack(side="left", padx=20, pady=12)
        tk.Label(top, text="Microplastics Monitor", font=("Courier", 10),
                 bg=PANEL_BG, fg=TEXT_FG).pack(side="left", pady=12)

        self.status_lbl = tk.Label(top, text="● DISCONNECTED",
                                   font=("Courier", 10, "bold"),
                                   bg=PANEL_BG, fg="#ff4d4d")
        self.status_lbl.pack(side="right", padx=20)

        # ── Main layout: sidebar + content ───────────────────────────────────
        main = tk.Frame(self.root, bg=DARK_BG)
        main.pack(fill="both", expand=True)

        sidebar = tk.Frame(main, bg=PANEL_BG, width=220, bd=0)
        sidebar.pack(side="left", fill="y", padx=(8,0), pady=8)
        sidebar.pack_propagate(False)

        content = tk.Frame(main, bg=DARK_BG)
        content.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        self._build_sidebar(sidebar)
        self._build_charts(content)

    def _build_sidebar(self, parent):
        def section(title):
            tk.Label(parent, text=title, font=("Courier", 9, "bold"),
                     bg=PANEL_BG, fg=ACCENT, anchor="w").pack(
                     fill="x", padx=10, pady=(14,2))
            tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=10)

        def btn(text, cmd, color=ACCENT, row_parent=None):
            b = tk.Button(
                row_parent or parent, text=text, command=cmd,
                bg=PANEL_BG, fg=color, activebackground=BORDER,
                activeforeground=color, relief="flat",
                font=("Courier", 9, "bold"), cursor="hand2",
                highlightthickness=1, highlightbackground=color,
                padx=8, pady=4
            )
            b.pack(fill="x", padx=10, pady=3)
            return b

        # ── Connection ───────────────────────────────────────────────────────
        section("SERIAL PORT")

        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_var = tk.StringVar(value=ports[0] if ports else "/dev/ttyUSB0")
        port_frame = tk.Frame(parent, bg=PANEL_BG)
        port_frame.pack(fill="x", padx=10, pady=4)
        ttk.Combobox(port_frame, textvariable=self.port_var,
                     values=ports, width=14,
                     font=("Courier", 9)).pack(side="left")
        tk.Button(port_frame, text="↺", command=self._refresh_ports,
                  bg=PANEL_BG, fg=ACCENT, relief="flat",
                  font=("Courier", 10), cursor="hand2").pack(side="left", padx=4)

        self.connect_btn = btn("CONNECT", self._connect, ACCENT)

        # ── Device Controls ───────────────────────────────────────────────────
        section("DEVICE CONTROL")

        row1 = tk.Frame(parent, bg=PANEL_BG)
        row1.pack(fill="x", padx=10, pady=2)

        self.stream_btn = tk.Button(
            row1, text="▶ START", command=self._cmd_start,
            bg=PANEL_BG, fg=OK_FG, activebackground=BORDER,
            activeforeground=OK_FG, relief="flat",
            font=("Courier", 9, "bold"), cursor="hand2",
            highlightthickness=1, highlightbackground=OK_FG,
            padx=6, pady=4, width=8
        )
        self.stream_btn.pack(side="left")

        self.stop_btn = tk.Button(
            row1, text="■ STOP", command=self._cmd_stop,
            bg=PANEL_BG, fg=WARN_FG, activebackground=BORDER,
            activeforeground=WARN_FG, relief="flat",
            font=("Courier", 9, "bold"), cursor="hand2",
            highlightthickness=1, highlightbackground=WARN_FG,
            padx=6, pady=4, width=8
        )
        self.stop_btn.pack(side="left", padx=6)

        btn("ZERO / BASELINE", self._cmd_zero, ACCENT)
        btn("RESET DEVICE", self._cmd_reset, "#ff4d4d")

        # Sample rate
        section("SAMPLE RATE")
        rate_frame = tk.Frame(parent, bg=PANEL_BG)
        rate_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(rate_frame, text="Interval (ms):", font=("Courier", 8),
                 bg=PANEL_BG, fg=TEXT_FG).pack(side="left")
        self.rate_var = tk.StringVar(value="500")
        tk.Entry(rate_frame, textvariable=self.rate_var, width=6,
                 bg=DARK_BG, fg=TEXT_FG, insertbackground=TEXT_FG,
                 font=("Courier", 9), relief="flat").pack(side="left", padx=4)
        tk.Button(rate_frame, text="SET", command=self._cmd_rate,
                  bg=PANEL_BG, fg=ACCENT, relief="flat",
                  font=("Courier", 8, "bold"), cursor="hand2").pack(side="left")

        # ── Live Readings ─────────────────────────────────────────────────────
        section("LIVE READINGS")

        self.reading_vars = {}
        readings = [
            ("MP Index", "mp_index", "pF RMS"),
            ("Temp",     "temp",     "°C"),
            ("Battery",  "bat",      "mV"),
            ("Samples",  "n",        ""),
        ]
        for label, key, unit in readings:
            row = tk.Frame(parent, bg=PANEL_BG)
            row.pack(fill="x", padx=10, pady=1)
            tk.Label(row, text=f"{label}:", font=("Courier", 8),
                     bg=PANEL_BG, fg=TEXT_FG, width=10, anchor="w").pack(side="left")
            var = tk.StringVar(value="—")
            self.reading_vars[key] = var
            tk.Label(row, textvariable=var, font=("Courier", 9, "bold"),
                     bg=PANEL_BG, fg=ACCENT, anchor="e").pack(side="left")
            tk.Label(row, text=unit, font=("Courier", 7),
                     bg=PANEL_BG, fg=TEXT_FG).pack(side="left", padx=2)

        # Alert label
        self.alert_lbl = tk.Label(parent, text="", font=("Courier", 9, "bold"),
                                  bg=PANEL_BG, fg=WARN_FG, wraplength=190)
        self.alert_lbl.pack(fill="x", padx=10, pady=8)

        # ── Export / Print ────────────────────────────────────────────────────
        section("EXPORT")
        btn("💾  SAVE CSV", self._export_csv, OK_FG)
        btn("🖨  PRINT REPORT", self._print_report, TEXT_FG)
        btn("📊  SAVE PLOTS", self._save_plots, TEXT_FG)

        # ── Status log ───────────────────────────────────────────────────────
        section("LOG")
        self.log_text = tk.Text(parent, height=6, bg=DARK_BG, fg=OK_FG,
                                font=("Courier", 7), relief="flat",
                                insertbackground=OK_FG, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=4)
        self.log_text.config(state="disabled")

    def _build_charts(self, parent):
        """Build the matplotlib dashboard embedded in Tkinter."""

        self.fig = plt.Figure(figsize=(9, 6), facecolor=DARK_BG, tight_layout=True)
        gs = gridspec.GridSpec(3, 2, figure=self.fig,
                               hspace=0.45, wspace=0.35,
                               left=0.08, right=0.97, top=0.93, bottom=0.08)

        ax_style = dict(facecolor=PANEL_BG)

        # [0,0] — Raw capacitance all 4 channels
        self.ax_raw = self.fig.add_subplot(gs[0, :], **ax_style)
        self.ax_raw.set_title("Raw Capacitance — All Channels",
                              color=TEXT_FG, fontsize=9, loc="left", pad=4)

        # [1,0] — Delta (deviation from baseline)
        self.ax_delta = self.fig.add_subplot(gs[1, 0], **ax_style)
        self.ax_delta.set_title("Δ Capacitance from Baseline",
                                color=TEXT_FG, fontsize=9, loc="left", pad=4)

        # [1,1] — Microplastic Index
        self.ax_mp = self.fig.add_subplot(gs[1, 1], **ax_style)
        self.ax_mp.set_title("Microplastic Index (pF RMS)",
                             color=TEXT_FG, fontsize=9, loc="left", pad=4)

        # [2,0] — Temperature
        self.ax_temp = self.fig.add_subplot(gs[2, 0], **ax_style)
        self.ax_temp.set_title("Temperature (°C)",
                               color=TEXT_FG, fontsize=9, loc="left", pad=4)

        # [2,1] — Battery voltage
        self.ax_bat = self.fig.add_subplot(gs[2, 1], **ax_style)
        self.ax_bat.set_title("Battery (mV)",
                              color=TEXT_FG, fontsize=9, loc="left", pad=4)

        for ax in [self.ax_raw, self.ax_delta, self.ax_mp,
                   self.ax_temp, self.ax_bat]:
            ax.tick_params(colors=TEXT_FG, labelsize=7)
            ax.xaxis.label.set_color(TEXT_FG)
            ax.yaxis.label.set_color(TEXT_FG)
            for spine in ax.spines.values():
                spine.set_color(BORDER)
            ax.set_xlabel("Time (s)", color=TEXT_FG, fontsize=7)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.grid(True, color=BORDER, linewidth=0.5, alpha=0.6)
            ax.grid(True, which="minor", color=BORDER,
                    linewidth=0.2, alpha=0.3)

        # Threshold line on MP plot
        self.thresh_line = self.ax_mp.axhline(
            DANGER_THRESH, color=WARN_FG, linewidth=1,
            linestyle="--", label=f"Alert >{DANGER_THRESH}")
        self.ax_mp.legend(fontsize=6, facecolor=PANEL_BG,
                          labelcolor=TEXT_FG, loc="upper left")

        # Pre-create line objects for fast update
        self.lines_raw   = [self.ax_raw.plot([], [], lw=1.2, color=c,
                             label=n)[0]
                             for c, n in zip(CHANNEL_COLS, CHANNEL_NAMES)]
        self.lines_delta = [self.ax_delta.plot([], [], lw=1.0, color=c,
                             label=n)[0]
                             for c, n in zip(CHANNEL_COLS, CHANNEL_NAMES)]
        self.line_mp,    = self.ax_mp.plot([], [], lw=1.5, color=MP_COL)
        self.line_temp,  = self.ax_temp.plot([], [], lw=1.2, color="#f4a261")
        self.line_bat,   = self.ax_bat.plot([], [], lw=1.2, color="#52b788")

        self.ax_raw.legend(fontsize=6, facecolor=PANEL_BG,
                           labelcolor=TEXT_FG, loc="upper left", ncol=4)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()

    # ── Connection Helpers ────────────────────────────────────────────────────

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        # Rebuild combobox values
        for w in self.root.winfo_children():
            pass  # tkinter doesn't expose combo easily — just log
        self._log(f"Ports: {ports or 'none found'}")

    def _connect(self):
        if self.reader and self.reader.is_alive():
            self.reader.stop()
            time.sleep(0.3)

        port = self.port_var.get().strip()
        self._log(f"Connecting to {port} @ {DEFAULT_BAUD}…")
        self.reader = SerialReader(port, self.args.baud, self.data_q)
        self.reader.start()
        time.sleep(0.5)
        if self.reader.connected:
            self.status_lbl.config(text=f"● {port}", fg=OK_FG)
            self.connect_btn.config(text="DISCONNECT", command=self._disconnect)
            self._log(f"Connected: {port}")
        else:
            self.status_lbl.config(text="● FAILED", fg="#ff4d4d")
            self._log("Connection failed — check port and device power.")

    def _disconnect(self):
        if self.reader:
            self.reader.stop()
        self.status_lbl.config(text="● DISCONNECTED", fg="#ff4d4d")
        self.connect_btn.config(text="CONNECT", command=self._connect)
        self._log("Disconnected.")

    # ── Device Commands ───────────────────────────────────────────────────────

    def _send(self, cmd: str):
        if self.reader and self.reader.connected:
            self.reader.send(cmd)
            self._log(f"→ {cmd}")
        else:
            self._log("Not connected.")

    def _cmd_start(self): self._send("CMD:START")
    def _cmd_stop(self):  self._send("CMD:STOP")
    def _cmd_zero(self):  self._send("CMD:ZERO")
    def _cmd_reset(self): self._send("CMD:RESET")

    def _cmd_rate(self):
        ms = self.rate_var.get().strip()
        self._send(f"CMD:RATE:{ms}")

    # ── Data Polling & Chart Update ───────────────────────────────────────────

    def _schedule_poll(self):
        self.root.after(100, self._poll)

    def _poll(self):
        """Drain the queue, push data, refresh UI."""
        updated = False
        for _ in range(50):                    # process up to 50 msgs per tick
            try:
                obj = self.data_q.get_nowait()
            except queue.Empty:
                break

            if "_error" in obj:
                self._log(f"ERROR: {obj['_error']}")
                self.status_lbl.config(text="● ERROR", fg="#ff4d4d")
            elif "_raw" in obj:
                self._log(obj["_raw"])
            elif "status" in obj:
                self._log(f"[device] {obj['status']}")
            elif "mp_index" in obj:
                self.store.push(obj)
                updated = True
                self._update_readings(obj)

        if updated:
            self._update_charts()

        if self._running:
            self._schedule_poll()

    def _update_readings(self, obj: dict):
        mp = obj.get("mp_index", 0.0)
        self.reading_vars["mp_index"].set(f"{mp:.5f}")
        self.reading_vars["temp"].set(f"{obj.get('temp', 0.0):.1f}")
        self.reading_vars["bat"].set(f"{obj.get('bat_mv', 0)}")
        self.reading_vars["n"].set(str(obj.get("n", 0)))

        if mp > DANGER_THRESH:
            self.alert_lbl.config(
                text=f"⚠ HIGH MP INDEX: {mp:.5f}\nPossible microplastic presence!",
                fg=WARN_FG)
        else:
            self.alert_lbl.config(text="✓ Within normal range", fg=OK_FG)

    def _update_charts(self):
        ts, ch, delta, mp, temp, bat = self.store.snapshot()
        if len(ts) < 2:
            return

        for i, line in enumerate(self.lines_raw):
            line.set_data(ts, ch[i])
        for i, line in enumerate(self.lines_delta):
            line.set_data(ts, delta[i])
        self.line_mp.set_data(ts, mp)
        self.line_temp.set_data(ts, temp)
        self.line_bat.set_data(ts, bat)

        for ax in [self.ax_raw, self.ax_delta, self.ax_mp,
                   self.ax_temp, self.ax_bat]:
            ax.relim()
            ax.autoscale_view()

        # Alert background on MP plot
        if mp.size > 0 and mp[-1] > DANGER_THRESH:
            self.ax_mp.set_facecolor("#2a1a0a")
        else:
            self.ax_mp.set_facecolor(PANEL_BG)

        self.canvas.draw_idle()

    # ── Export / Print ────────────────────────────────────────────────────────

    def _export_csv(self):
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        default = LOG_DIR / f"nira_{ts_str}.csv"
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=str(default),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not path:
            return
        if self.store.export_csv(Path(path)):
            self._log(f"CSV saved: {path}")
            messagebox.showinfo("Export", f"Data saved to:\n{path}")
        else:
            messagebox.showwarning("Export", "No data to export yet.")

    def _save_plots(self, path: str = None):
        """Save a high-res PNG of all plots."""
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not path:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=str(LOG_DIR / f"nira_plots_{ts_str}.png"),
                filetypes=[("PNG", "*.png"), ("All files", "*.*")]
            )
        if not path:
            return
        self.fig.savefig(path, dpi=200, facecolor=DARK_BG,
                         bbox_inches="tight")
        self._log(f"Plots saved: {path}")
        return path

    def _print_report(self):
        """
        Generate a standalone printable matplotlib figure with:
          - Summary statistics table
          - All channel plots
          - MP index plot with threshold
        Opens as a separate window with a Print/Save PDF button.
        """
        ts, ch, delta, mp, temp, bat = self.store.snapshot()
        if len(ts) < 2:
            messagebox.showwarning("Print", "Not enough data to print.")
            return

        now_str  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        n_pts    = len(ts)
        duration = ts[-1] - ts[0]

        # ── Build print figure ────────────────────────────────────────────────
        pfig = plt.figure(figsize=(11.7, 8.27), facecolor="white")  # A4 landscape
        pfig.suptitle(
            f"Project Nira — Microplastics Analysis Report\n"
            f"Generated: {now_str}  |  Samples: {n_pts}  |  Duration: {duration:.1f} s",
            fontsize=12, fontweight="bold", color="#0d1b2a", y=0.98
        )

        pgs = gridspec.GridSpec(3, 2, figure=pfig,
                                hspace=0.55, wspace=0.35,
                                left=0.08, right=0.97,
                                top=0.88, bottom=0.12)

        pax_style = dict(facecolor="white")

        # Raw capacitance (full width)
        ax_r = pfig.add_subplot(pgs[0, :], **pax_style)
        for i in range(4):
            ax_r.plot(ts, ch[i], lw=1.0, label=CHANNEL_NAMES[i],
                      color=CHANNEL_COLS[i])
        ax_r.set_title("Raw Capacitance (pF) — All Channels",
                        fontsize=10, loc="left")
        ax_r.set_xlabel("Time (s)"); ax_r.set_ylabel("pF")
        ax_r.legend(fontsize=8, ncol=4); ax_r.grid(True, alpha=0.3)

        # Delta
        ax_d = pfig.add_subplot(pgs[1, 0], **pax_style)
        for i in range(4):
            ax_d.plot(ts, delta[i], lw=1.0, label=CHANNEL_NAMES[i],
                      color=CHANNEL_COLS[i])
        ax_d.set_title("Δ Capacitance from Baseline (pF)", fontsize=10, loc="left")
        ax_d.set_xlabel("Time (s)"); ax_d.set_ylabel("ΔpF")
        ax_d.legend(fontsize=8, ncol=2); ax_d.grid(True, alpha=0.3)

        # MP Index
        ax_m = pfig.add_subplot(pgs[1, 1], **pax_style)
        ax_m.plot(ts, mp, lw=1.5, color="#c9184a", label="MP Index")
        ax_m.axhline(DANGER_THRESH, color="#f77f00", ls="--", lw=1,
                     label=f"Alert threshold ({DANGER_THRESH})")
        ax_m.fill_between(ts, mp, where=mp > DANGER_THRESH,
                          alpha=0.2, color="#f77f00", label="Above threshold")
        ax_m.set_title("Microplastic Index (pF RMS)", fontsize=10, loc="left")
        ax_m.set_xlabel("Time (s)"); ax_m.set_ylabel("pF RMS")
        ax_m.legend(fontsize=7); ax_m.grid(True, alpha=0.3)

        # Stats table
        ax_t = pfig.add_subplot(pgs[2, :])
        ax_t.axis("off")
        stat_data = []
        col_labels = ["Channel / Metric", "Min", "Max", "Mean", "Std Dev", "Unit"]
        for i in range(4):
            row = [
                CHANNEL_NAMES[i],
                f"{ch[i].min():.4f}", f"{ch[i].max():.4f}",
                f"{ch[i].mean():.4f}", f"{ch[i].std():.4f}", "pF"
            ]
            stat_data.append(row)
        stat_data.append([
            "MP Index",
            f"{mp.min():.5f}", f"{mp.max():.5f}",
            f"{mp.mean():.5f}", f"{mp.std():.5f}", "pF RMS"
        ])
        if temp.size > 0 and not np.isnan(temp).all():
            stat_data.append([
                "Temperature",
                f"{temp.min():.1f}", f"{temp.max():.1f}",
                f"{temp.mean():.1f}", f"{temp.std():.1f}", "°C"
            ])

        tbl = ax_t.table(cellText=stat_data, colLabels=col_labels,
                         loc="center", cellLoc="center")
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(9)
        tbl.scale(1, 1.5)
        for (r, c), cell in tbl.get_celld().items():
            if r == 0:
                cell.set_facecolor("#0d1b2a")
                cell.set_text_props(color="white", fontweight="bold")
            elif r % 2 == 0:
                cell.set_facecolor("#e8f4fd")
        ax_t.set_title("Summary Statistics Table", fontsize=10,
                        loc="left", pad=8)

        # ── Show in window ────────────────────────────────────────────────────
        win = tk.Toplevel(self.root)
        win.title("Print Preview — Project Nira Report")
        win.configure(bg="white")

        pcanvas = FigureCanvasTkAgg(pfig, master=win)
        pcanvas.get_tk_widget().pack(fill="both", expand=True)
        pcanvas.draw()

        btn_frame = tk.Frame(win, bg="white")
        btn_frame.pack(fill="x", pady=6)

        def save_pdf():
            ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=f"nira_report_{ts_str}.pdf",
                filetypes=[("PDF", "*.pdf"), ("PNG", "*.png"),
                            ("All files", "*.*")]
            )
            if path:
                pfig.savefig(path, dpi=200, bbox_inches="tight",
                             facecolor="white")
                messagebox.showinfo("Saved", f"Report saved:\n{path}")
                self._log(f"Report saved: {path}")

        tk.Button(btn_frame, text="💾  Save PDF / PNG", command=save_pdf,
                  bg="#0d1b2a", fg="white", font=("Courier", 10, "bold"),
                  padx=16, pady=6, relief="flat", cursor="hand2").pack(
                  side="right", padx=16)
        tk.Button(btn_frame, text="✕  Close", command=win.destroy,
                  bg="#e0e0e0", fg="#333", font=("Courier", 9),
                  padx=12, pady=6, relief="flat", cursor="hand2").pack(
                  side="right", padx=4)

    # ── Utility ───────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"
        self.log_text.config(state="normal")
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def on_close(self):
        self._running = False
        if self.reader:
            self.reader.stop()
        plt.close("all")
        self.root.destroy()


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Project Nira — Microplastics Monitor GUI"
    )
    parser.add_argument("--port", default="",
                        help="Serial port (e.g. /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD,
                        help="Baud rate (default: 115200)")
    args = parser.parse_args()

    root = tk.Tk()
    app  = NiraApp(root, args)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
