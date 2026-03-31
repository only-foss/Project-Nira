# Data Analysis

Project Nira uses a GNU Octave script to analyze the differential capacitance signal from the FDC1004.

## Scripts
- **`nira_analysis.m`**: The primary GNU Octave analysis script located in `tests/analysis/`.
- **`python/nira_reader.py`**: A python script that pulls from an InfluxDB server seamlessly.
- **`python/nira_dashboard.py`**: A robust Python dashboard (GUI and CLI) that gathers data from the ESP32 via USB serial in real-time. Use this if you don't want to use WiFi/InfluxDB. 
  - CLI usage: `python python/nira_dashboard.py --cli --port /dev/ttyUSB0`

## Reproduce Results
Run the following locally:
```bash
cd tests/analysis/
octave nira_analysis.m
```
