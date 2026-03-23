# Changelog — Project Nira

All notable changes to this project are documented here.  
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | Versioning: [SemVer](https://semver.org/)

---

## [v1.0] — 2026-03-22 — First Validated Prototype

### Hardware
- ESP32 DevKit v1 + ProtoCentral FDC1004 Breakout v3 breadboard prototype
- 2× copper plate electrodes as capacitance sensing elements
- KiCad schematic and PCB layout (v1.0)
- Custom KiCad symbols: `ESP32-DEVKIT-V1.kicad_sym`, `PC-FDC1004-v3.kicad_sym`
- STEP 3D models added for ESP32 and FDC1004
- BOM.csv with component sourcing details
- Wiring notes (`WIRING_NOTES.md`) for breadboard connections

### Firmware
- Arduino sketch `nira_esp32.ino` for ESP32 + FDC1004
- Reads CH1 and CH4 raw capacitance values via I2C
- Computes differential signal: `diff_c1_c4 = CH1 − CH4`
- Logs data to InfluxDB over WiFi at 10-second intervals
- Tagged with `device=nira_esp32`, measurement `nira_sensor`

### Testing
- Test 0: Clean water — 55 samples collected (2026-03-22)
- Test 1: Water with microplastics — 42 samples collected (2026-03-22)
- Raw InfluxDB CSV exports stored in `tests/data/`
- Pivoted analysis CSVs in `tests/analysis/`

### Analysis
- GNU Octave analysis suite — zero external packages required
- `nira_analysis.m` — main entry point, statistics, Welch t-test
- `nira_plot_timeseries.m` — CH1, CH4, diff time-series (3 panels)
- `nira_plot_comparison.m` — mean ± σ bar chart + hand-drawn box plot
- `nira_plot_histogram.m` — overlapping histograms + Gaussian fits
- `nira_plot_scatter.m` — CH1 vs CH4 directional scatter
- All plots saved to `tests/results/` at 150 DPI
- GPL-3.0 SPDX headers and function docstrings added to all `.m` files

### Validated Results
| Metric | Value |
|--------|-------|
| Clean water mean diff_c1_c4 | −193.6 ADC |
| Microplastic mean diff_c1_c4 | +377.8 ADC |
| Signal shift | +571 ADC (4.4σ above clean baseline) |
| Welch t-test p-value | 3.24×10⁻⁴⁵ |
| Detection threshold | diff_c1_c4 > 92 ADC units |

### Documentation
- `README.md` — full project overview with wiring, stats, quick start
- `CONTRIBUTING.md` — contribution workflow, branch naming, hardware rules
- `CITATION.cff` — academic citation metadata
- `CHANGELOG.md` — this file
- `docs/OVERVIEW.md` — project background and goals
- `docs/USAGE.md` — step-by-step usage instructions
- `docs/ARCHITECTURE.md` — system architecture and design decisions
- `hardware/breadboard/WIRING_NOTES.md` — pin connections table
- `tests/README_analysis.md` — how to run the Octave analysis
- CERN-OHL-P v2 hardware license confirmed

---

## [Unreleased] — In Progress

### Planned for v1.1
- [ ] Export Gerber files to `hardware/v1.0_esp32_sensor/pcb/`
- [ ] PCB design to replace breadboard prototype
- [ ] `python/nira_reader.py` — InfluxDB data export utility
- [ ] `python/requirements.txt` — Python dependencies
- [ ] draw.io wiring diagram (`hardware/breadboard/wiring_diagram.png`)
- [ ] `.gitattributes` — fix language detection (Octave not MATLAB)
- [ ] IP67 enclosure CAD files in `mechanical/`
- [ ] Firmware dependency list (`libraries.txt` or `platformio.ini`)
- [ ] OSHWA certification submission
- [ ] GitHub Release tag `v1.0`
- [ ] Issue templates (`.github/ISSUE_TEMPLATE/`)

### Planned for v2.0
- [ ] ESP32-S3 + ADS131M08 24-bit ADC upgrade
- [ ] IP67 waterproof enclosure (field deployment ready)
- [ ] BLE/WiFi configuration portal
- [ ] On-device detection algorithm
- [ ] Flow-through sample chamber
- [ ] Mobile app or web dashboard

---

## Notes on versioning

- **v1.x** — ESP32 DevKit v1 + FDC1004 platform
- **v2.x** — ESP32-S3 + ADS131M08 platform (planned)
- Hardware and firmware versions tracked independently from documentation versions
