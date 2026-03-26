# Contributing to Project Nira

> Open Hardware Microplastics Detector — [github.com/only-foss/Project-Nira](https://github.com/only-foss/Project-Nira)

Thank you for your interest in Project Nira. All contributions — hardware, firmware, software, documentation, testing, and translations — are equally valued.

---

## Ways to Contribute

### Hardware
- Improve electrode geometry or materials
- Design a proper PCB (currently breadboard prototype)
- Design an IP67 enclosure for field deployment
- Validate sensor performance with different microplastic types/sizes

### Firmware
- Improve FDC1004 sampling rate and averaging
- Add BLE/WiFi configuration portal
- Implement on-device threshold detection and alert

### Software & Analysis
- Improve GNU Octave analysis scripts in `tests/analysis/`
- Add Python analysis pipeline
- Implement ML classification of sensor data

### Documentation
- Translate docs (priority: Hindi, Marathi, Tamil)
- Add build tutorials with photos
- Write a field deployment guide

---

## Workflow

1. Open a **GitHub Issue or Discussion** describing what you plan to do
2. Fork the repo and create a branch: `git checkout -b feat/your-feature`
3. Make focused commits with clear messages
4. Update documentation as needed
5. Submit a **Pull Request** with a clear description

### Branch naming

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/pcb-v2-layout` |
| Bug fix | `fix/description` | `fix/fdc1004-i2c-timeout` |
| Documentation | `docs/description` | `docs/hindi-translation` |
| Hardware | `hw/description` | `hw/enclosure-v1` |
| Tests | `test/description` | `test/saltwater-validation` |

---

## Hardware Contribution Rules

- All hardware must be licensed under **CERN-OHL-P v2**
- Include KiCad source files — PDFs alone are not sufficient
- Include `BOM.csv` with supplier, part number, quantity, and reference designator
- Version hardware as `vX.Y` (e.g. `v1.1`, `v2.0`)
- Export Gerbers to `hardware/vX.Y/pcb/` for PCB designs

---

## Code of Conduct

Be kind. Be constructive. Be collaborative. This project is built for communities that lack access to environmental monitoring — please bring that spirit to all interactions.

Questions? Open a [GitHub Discussion](https://github.com/only-foss/Project-Nira/discussions).
