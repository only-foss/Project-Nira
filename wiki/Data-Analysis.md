# Data Analysis

Project Nira uses a GNU Octave script to analyze the differential capacitance signal from the FDC1004.

## Scripts
- **`nira_analysis.m`**: The primary analysis script located in `tests/analysis/`. It loads raw `.csv` InfluxDB exports, calculates the signal significance (Welch t-test), and generates four high-quality plots found in `tests/results/`.
- **`python/nira-reader.py`**: A python script that allows users to export data seamlessly without relying on the cloud dashboard. 

## Reproduce Results
Run the following locally:
```bash
cd tests/analysis/
octave nira_analysis.m
```
