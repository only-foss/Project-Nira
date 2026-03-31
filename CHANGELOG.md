# Changelog — Project Nira

All notable changes to this project will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/)
Versioning: [Semantic Versioning](https://semver.org/)

## [1.1.0] — 2026-01-01

### Added
- Structured JSON serial output protocol (nira-serial-v1)
- `CMD:START`, `CMD:STOP`, `CMD:ZERO`, `CMD:RATE`, `CMD:RESET` command parser
- 32-sample baseline averaging (`capture_baseline()`)
- Microplastic index (`mp_index`) = RMS delta from baseline
- Battery voltage ADC readout (`bat_mv`)
- Internal temperature sensor readout (`temp`)
- Python real-time GUI (`software/nira_gui.py`)
- 5-panel live dashboard (raw pF, delta pF, MP index, temp, battery)
- One-click printable PDF/PNG report with statistics table
- One-click CSV data export
- Serial command control panel in GUI
- Alert system: amber highlight + sidebar warning when mp_index > 0.10
- `docs/SERIAL_PROTOCOL.md` — full protocol reference
- `docs/FIRMWARE_API.md` — firmware function reference
- `docs/GUI_USER_GUIDE.md` — end-user GUI guide
- `docs/CALIBRATION.md` — calibration and zeroing procedure
- `requirements.txt` — pinned Python dependencies
- `platformio.ini` — pinned PlatformIO build config
- `CONTRIBUTING.md`, GitHub issue templates

### Changed
- Firmware version bumped to nira-v1.1
- Serial output changed from ad-hoc prints to JSON protocol

## [1.0.0] — 2025-12-01

### Added
- Initial ESP32-S3 + FDC1004 firmware
- 4-channel capacitance reading
- Basic serial output
- KiCad schematics v1.0
