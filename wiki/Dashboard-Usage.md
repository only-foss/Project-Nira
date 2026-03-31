# Full GUI Dashboard & CLI Tool

Project Nira provides a complete Python-based Dashboard utility (`nira_dashboard.py`) to streamline testing and evaluation. It handles live plotting, real-time parameters, and local data collection seamlessly directly from the ESP32’s micro-USB port, skipping Wi-Fi connectivity if preferred.

## Requirements
Ensure you have the required dependencies installed on your system.
```bash
cd Project-Nira
pip install -r python/requirements.txt
```
*(The Dashboard specifically requires `pyserial`, `pandas`, and `matplotlib`.)*

## Option 1: GUI Dashboard Mode

To launch the graphical interface, run the script with no arguments (or pass specific defaults):

```bash
# Launch the desktop UI
python python/nira_dashboard.py
```

### Features
*   **Connection Panel:** Select the correct serial port (e.g., `COM3`, `/dev/ttyUSB0`) and Baud Rate (Default `115200`). Click "Connect".
*   **Data Logging Panel:** Choose where to save your `.csv` file locally (e.g., `nira_test_run.csv`). Click "Start Local Logging" to commence collecting. You can toggle this on and off without losing data.
*   **Parameters Panel:** Control settings like the Live Plot "Window Size" (how many samples look back in history) in real-time. Apply them to dynamically adjust the UI without disconnecting.
*   **Live Signals View:** Hardware-accelerated Matplotlib plotting rendering 100 Hz signals.
    *   **Top Plot:** `CH1` and `CH4` baseline capacitance outputs.
    *   **Bottom Plot:** The generated particle detection "Differential Signal".

## Option 2: Headless CLI Mode

For headless setups (like Raspberry Pi zero deployments) or scripting, the tool offers a `--cli` mode. This records the live USB output directly into your designated CSV without creating UI windows.

```bash
# Launch in CLI mode, specifying port and output file
python python/nira_dashboard.py --cli --port /dev/ttyUSB0 --baud 115200 --out test_01.csv
```

### CLI Output
The console will log debug connection messages and then begin streaming the converted particle detection strings:
`[DATA] ms:4219 | CH1:327 | CH4:255 | Diff:72 | Temp:25.0`

## Important Notes
- **Dependencies Dropback:** If you attempt to run the GUI mode but your Python environment lacks `tkinter` or `matplotlib`, the script will gracefully error-catch and fallback completely into **CLI Mode**.
- The dashboard is primarily meant to serve **v1.5 and newer** firmware. Please ensure your ESP32 is flashing the correct PlatformIO codebase.
