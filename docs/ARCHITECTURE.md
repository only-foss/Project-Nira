# Architecture — Project Nira

> System design, component decisions, and data flow for the v1.0 prototype.

---

## System Overview

Project Nira detects microplastics in water by measuring the **dielectric difference**
between clean water and microplastic-contaminated water using capacitance sensing.
The key insight is that microplastic particles change the effective permittivity of
the water sample, which shows up as a measurable shift in the differential capacitance
reading between two electrode channels.

```
┌─────────────────────────────────────────────────────────────┐
│                     Project Nira v1.0                       │
│                                                             │
│  [Electrodes]──[FDC1004]──I2C──[ESP32]──WiFi──[InfluxDB]   │
│                                    │                        │
│                              [Grafana Dashboard]            │
└─────────────────────────────────────────────────────────────┘
```

---

## Hardware Architecture

### Sensing Chain

```
Water Sample
    │
    ├── Copper Electrode 1 (CIN1) ──┐
    │                               ├── FDC1004 ── I2C ── ESP32
    └── Copper Electrode 2 (CIN4) ──┘
```

| Stage | Component | Role |
|-------|-----------|------|
| Sensing element | 2× copper plate electrodes | Convert dielectric change to capacitance |
| ADC | ProtoCentral FDC1004 Breakout v3 | 4-channel capacitance-to-digital converter |
| Microcontroller | ESP32 DevKit v1 | I2C master, WiFi, data logging |
| Communication | WiFi 802.11 b/g/n | Transmit readings to InfluxDB |
| Storage | InfluxDB (time-series DB) | Store and query sensor data |
| Visualisation | Grafana | Real-time dashboard |

### Why FDC1004?

The Texas Instruments FDC1004 was chosen for v1.0 because:
- 4 independent capacitance channels (we use CH1 and CH4)
- 16-bit resolution, ±15pF range
- I2C interface — easy to wire to ESP32
- Low cost, available on ProtoCentral breakout board
- Fixed I2C address `0x50` — no address conflicts
- Differential measurement between channels eliminates common-mode noise

### Why differential sensing (CH1 − CH4)?

Using two channels and computing `diff_c1_c4 = CH1 − CH4` rather than a single
channel reading provides:
- Cancellation of temperature drift (both channels affected equally)
- Cancellation of common electrical noise
- A signed detection metric: negative = clean water, positive = microplastics
- Higher SNR than single-ended measurement

### Detection threshold

Based on v1.0 test results:
- Clean water: mean diff = −193.6 ADC, std = 128.6
- Microplastics: mean diff = +377.8 ADC, std = 69.9
- Threshold: **diff_c1_c4 > 92 ADC units** (midpoint between means)
- Separation: 4.4σ — zero overlap between distributions

---

## Firmware Architecture

### Stack

```
Arduino Framework (ESP32)
    │
    ├── Wire.h          — I2C communication with FDC1004
    ├── WiFi.h          — WiFi connection
    ├── InfluxDBClient  — Time-series data upload
    └── ProtoCentral FDC1004 library — sensor abstraction
```

### Data flow

```
loop() every 10s
    │
    ├── read CH1 raw from FDC1004 via I2C
    ├── read CH4 raw from FDC1004 via I2C
    ├── compute diff_c1_c4 = CH1 - CH4
    └── write to InfluxDB:
            measurement: nira_sensor
            tags:        device=nira_esp32, team=domination
            fields:      ch1_raw, ch4_raw, diff_c1_c4
            timestamp:   current UTC
```

### InfluxDB data model

```
measurement: nira_sensor
├── tag: device   = nira_esp32
├── tag: team     = domination
├── field: ch1_raw      (float)
├── field: ch4_raw      (float)
└── field: diff_c1_c4   (float)
```

---

## Analysis Architecture

### Pipeline

```
InfluxDB export (CSV)
    │
    ├── python/nira_reader.py     — automated export (planned v1.1)
    │   OR manual CSV export from InfluxDB UI
    │
    └── tests/analysis/
            │
            ├── nira_analysis.m         — load, stats, t-test, call plots
            ├── nira_plot_timeseries.m  — time-series visualisation
            ├── nira_plot_comparison.m  — bar chart + box plot
            ├── nira_plot_histogram.m   — distribution + Gaussian fit
            └── nira_plot_scatter.m     — CH1 vs CH4 scatter
                    │
                    └── tests/results/
                            ├── nira_01_timeseries.png
                            ├── nira_02_comparison.png
                            ├── nira_03_histogram.png
                            └── nira_04_scatter.png
```

### GNU Octave — why no external packages?

All analysis scripts use only **base GNU Octave built-ins**:
- `textscan` — CSV loading (no `csv2cell` which needs `io` package)
- `betainc` — p-value calculation (no `ttest2` which needs `statistics` package)
- `patch` + `plot` — all visualisations (no `boxplot`, no `scatter` alpha)

This ensures the analysis runs on any GNU Octave installation with zero setup.

---

## Repository Architecture

```
Project-Nira/
│
├── Root files              — GitHub-standard files (README, LICENSE, etc.)
├── assets/                 — Photos, screenshots (not referenced in code)
├── docs/                   — Detailed documentation
├── firmware/vX.Y/          — Versioned firmware source
├── hardware/vX.Y/          — Versioned hardware design files
│   ├── breadboard/         — Wiring docs for prototype builds
│   ├── cad/                — 3D models and KiCad symbols
│   ├── pcb/                — Gerber fabrication outputs
│   └── Nira_.../           — KiCad project folder
├── mechanical/             — Enclosure CAD (planned v1.1)
├── python/                 — Data utilities (planned v1.1)
└── tests/
    ├── analysis/           — Octave scripts + input CSVs
    ├── data/               — Raw InfluxDB exports
    ├── photos/             — Physical test setup photos
    └── results/            — Generated plot outputs
```

### Versioning strategy

Hardware and firmware are versioned independently using `vMAJOR.MINOR`:
- `v1.0` — initial validated prototype
- `v1.1` — PCB, Gerbers, enclosure (planned)
- `v2.0` — new sensing platform ESP32-S3 + ADS131M08 (planned)

Each version gets its own subfolder so older versions remain accessible.

---

## Design Decisions & Trade-offs

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Sensing method | Capacitance (FDC1004) | Impedance spectroscopy | Lower cost, simpler wiring |
| MCU | ESP32 DevKit v1 | Raspberry Pi, Arduino | WiFi built-in, low cost, Arduino compatible |
| Data storage | InfluxDB | SD card, serial | Remote access, time-series optimised |
| Analysis tool | GNU Octave | Python/pandas | FOSS, no install friction, .m files readable |
| License | CERN-OHL-P | CERN-OHL-S, CC | Permissive — allows commercial use with attribution |
| Build form | Breadboard (v1.0) | Custom PCB | Faster iteration, lower barrier to reproduce |

---

## Known Limitations — v1.0

- Breadboard prototype — not weatherproof or field-deployable
- No on-device detection — requires external InfluxDB + analysis
- Electrode geometry not optimised — copper plates, not interdigitated
- Single sample type tested — needs validation with different microplastic types
- No flow-through chamber — static water sample only
- WiFi required — no offline / BLE mode yet
- FDC1004 range ±15pF — may need ADS131M08 for higher sensitivity (v2.0)

---

## References

- FDC1004 Datasheet: [ti.com/product/FDC1004](https://www.ti.com/product/FDC1004)
- ProtoCentral FDC1004 library: [github.com/protocentral/ProtoCentral_fdc1004_breakout](https://github.com/protocentral/ProtoCentral_fdc1004_breakout)
- CERN-OHL-P v2: [cern-ohl.web.cern.ch](https://cern-ohl.web.cern.ch/)
- OSHW Definition: [oshwa.org/definition](https://www.oshwa.org/definition/)
- GNU Octave: [octave.org](https://octave.org/)
