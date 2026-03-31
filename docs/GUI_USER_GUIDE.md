# Project Nira — GUI User Guide
_nira_gui.py v1.1_

## Installation

```bash
# 1. Install Python dependencies
pip install pyserial matplotlib numpy

# 2. Tkinter (Linux only)
sudo apt install python3-tk

# 3. Run
python software/nira_gui.py --port /dev/ttyUSB0
# Windows:
python software/nira_gui.py --port COM4
```

## Offline Install

```bash
# Networked machine: download wheels
pip download pyserial matplotlib numpy -d ./wheels

# Offline machine:
pip install --no-index --find-links=./wheels pyserial matplotlib numpy
```

## Quick Start

1. Connect ESP32 via USB
2. Run `python software/nira_gui.py`
3. Select port → click **CONNECT**
4. Click **▶ START**
5. Place electrodes in clean water → click **ZERO / BASELINE**
6. Place electrodes in sample → watch MP Index

## Controls

| Control | Command Sent | Action |
|---------|-------------|--------|
| ▶ START | `CMD:START` | Begin streaming |
| ■ STOP | `CMD:STOP` | Pause streaming |
| ZERO / BASELINE | `CMD:ZERO` | Re-baseline in clean water |
| RESET DEVICE | `CMD:RESET` | Firmware restart |
| SET (interval) | `CMD:RATE:<ms>` | Change sample rate |
| ↺ | — | Refresh port list |

## Charts

| Chart | Data | Update |
|-------|------|--------|
| Raw Capacitance | ch0–ch3 (pF) | Every sample |
| Δ Capacitance | d0–d3 (pF delta from baseline) | Every sample |
| Microplastic Index | mp_index (pF RMS) | Every sample |
| Temperature | temp (°C) | Every sample |
| Battery | bat_mv (mV) | Every sample |

Rolling window: last **600 samples**.

## Alert System

When `mp_index > 0.10 pF RMS`:
- MP Index chart background turns amber
- Sidebar shows: **⚠ HIGH MP INDEX**

Threshold is configurable: edit `DANGER_THRESH` in `nira_gui.py`.

## Print Report (One Click)

Click **🖨 PRINT REPORT** → preview window opens with:
- Raw capacitance plot (all 4 channels)
- Delta capacitance plot
- MP Index plot with threshold band
- Summary statistics table (min/max/mean/std per channel)

Click **💾 Save PDF / PNG** to export. A4 landscape, 200 DPI.

## CSV Export

Click **💾 SAVE CSV** → save to `nira_logs/nira_YYYYMMDD_HHMMSS.csv`

Columns: `datetime, ts_s, n, ch0_pF, ch1_pF, ch2_pF, ch3_pF, d0_pF, d1_pF, d2_pF, d3_pF, mp_index, temp_c, bat_mv`

## Screenshot
![GUI Screenshot](../assets/gui_screenshot.png)
_(Replace with actual screenshot before submission)_
