# Project Nira

**Microplastics Detection Ecosystem**

[![License: CERN-OHL-P](https://img.shields.io/badge/Hardware-CERN--OHL--P%20v2-blue?style=flat-square)](https://cern-ohl.web.cern.ch/)
[![License: MIT](https://img.shields.io/badge/Software-MIT-blue?style=flat-square)](https://opensource.org/licenses/MIT)

Project Nira is an open-source, affordable (~$30 USD) IoT hardware and software stack designed to detect microplastics in water using capacitance-based differential sensing.

## 1. Overview
Conventional microplastic detection requires expensive spectroscopy equipment, lab preparation, and trained specialists. Project Nira solves this through a field-ready hardware edge-device that streams raw dielectric capacitance measurements to a local telemetry dashboard or a predictive Random Forest Classifier.

## 2. Directory Structure
- `firmware/`: Edge-device ESP32 C++ code.
- `hardware/`: KiCad PCB designs and schematics.
- `python/`: Dashboard UI, ML pipeline, and dependencies.
- `tests/`: Data logs and GNU Octave analysis scripts.
- `docs/`: Extra architectural specifications.

---

## 3. Installation (One-Command Setup)
We have designed the environment to be **completely automatic** for Windows and Linux/macOS. 
It uses `uv` to intelligently manage Python versions (3.12) and install dependencies locally safely.

**Windows Users:**
Double-click `setup.bat` or run in Command Prompt:
```cmd
setup.bat
```

**Linux / macOS Users:**
Open a terminal and run:
```bash
chmod +x setup.sh
./setup.sh
```

*(This automatically configures your Virtual Environment and VS Code settings for you!)*

---

## 4. Usage

### Launching the Dashboard (Inference / Telemetry)
The unified GUI dashboard connects to the ESP32 and visualizes raw analytics.

**Windows:**
```cmd
.venv\Scripts\activate
python python\nira_dashboard.py
```

**Linux / macOS:**
```bash
source .venv/bin/activate
python python/nira_dashboard.py
```

### Headless CLI Logging
For servers without graphical UIs, use `--cli`:
```bash
python python/nira_dashboard.py --cli --port /dev/ttyUSB0 --baud 115200 --out logs_test.csv
```

### Machine Learning Training
To retrain the Random Forest model on your custom datasets:
```bash
python python/ml_pipeline/train_model.py
```
*(Model weights will export to `model_export/nira_mp_rf_model.pkl`)*

---

## 5. Common Issues & Solutions
- **"ModuleNotFoundError: No module named..."**
  You haven't activated the virtual environment! Make sure you run `source .venv/bin/activate` (Linux) or `.venv\Scripts\activate` (Windows) before running the python script.
- **"Permission denied: /dev/ttyUSB0" (Linux)**
  Add your user to the dialout group safely via: `sudo usermod -aG dialout $USER`. Then log out and log back in.
- **"Cannot open Serial Port"**
  Ensure the ESP32 is plugged in with a data-capable micro-USB/USB-C cable (not charge-only), and close the Arduino IDE Serial Monitor (only one app can use the port at a time).

## 6. License
* **Hardware**: CERN-OHL-P v2
* **Software**: MIT
* **Documentation**: CC BY-SA 4.0
