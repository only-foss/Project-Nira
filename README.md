[![CERN-OHL-P](https://img.shields.io/badge/License-CERN--OHL--P-yellow.svg)](https://cern-ohl.web.cern.ch/)
[![OSHW](https://img.shields.io/badge/OSHW-Compliant-brightgreen)](https://certification.oshwa.org/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

# Project Nira: Open Hardware Microplastics Detector

**Project Nira** is an affordable (₹2500), portable impedance-based sensor designed to detect microplastics (<5mm) in water. It serves as a field-ready alternative to expensive lab spectrometers for schools and community groups.

## 🛠️ Quick Start

### 1. Requirements
- Python 3.12+
- `uv` (recommended) or `pip`
- OS: Linux, macOS, or Windows

### 2. Installation
Run the automated setup for your environment:

```bash
# Linux/macOS
./setup.sh

# Windows
.\setup.bat
```

### 3. Usage
```bash
source .venv/bin/activate
python python/nira_dashboard.py
```

## ⚙️ Architecture
The system uses **electrical impedance spectroscopy** to identify suspended microplastics.

1.  **Hardware**: ESP32-S3 + ADS131M08 (24-bit ADC) + 316L stainless steel electrodes.
2.  **Firmware**: ESP-IDF handling 1ksps data acquisition with BLE/WiFi streaming.
3.  **Software**: Python-based pipeline for signal processing and real-time visualization.

## 📁 Repository Structure
```text
├── assets/             # Images and branding
├── firmware/           # ESP32-S3 firmware source
├── hardware/           # KiCad schematics and CAD files
├── ml_pipeline/        # Signal analysis and models
├── python/             # Dashboard and user-facing tools
├── setup.sh            # Automated Linux setup
└── setup.bat           # Automated Windows setup
```

## 🌊 Why This Matters
Traditional microplastic monitoring is inaccessible due to high equipment costs (₹10L+) and complex sample prep. Project Nira provides a **repairable, modular, and open-source** tool for localized water quality monitoring.

## 📄 License
- **Software**: [MIT License](LICENSE.md#software)
- **Hardware**: [CC BY-SA 4.0 International](LICENSE.md#hardware)

---
*Built for FOSS Hack 2026 by Tram Dominators.*



