# Project Nira – GNU Octave Analysis

Sensor test analysis for the **Nira microplastic detection sensor**  
Device: `nira_esp32` | Measurement: `nira_sensor`  
by [only-foss](https://github.com/only-foss/Project-Nira)

---

## Test Conditions

| File | Condition | Samples |
|------|-----------|---------|
| `test-0_cleanWater.csv` | Clean water (baseline) | 55 |
| `test-1_water_with_microplastics.csv` | Water with microplastics | 42 |

## Sensor Channels

| Field | Description |
|-------|-------------|
| `ch1_raw` | Channel 1 – ADC raw reading |
| `ch4_raw` | Channel 4 – ADC raw reading |
| `diff_c1_c4` | CH1 − CH4 differential (primary detection feature) |

Data exported from InfluxDB (annotated CSV format).

---

## Key Finding

The **differential signal `diff_c1_c4`** cleanly separates both conditions:

| Condition | Mean diff | Std |
|-----------|-----------|-----|
| Clean water | **−193.6 ADC** | 128.6 |
| Microplastics | **+377.8 ADC** | 69.9 |

- Shift: **+571 ADC units** (~4.4σ above clean baseline)
- Suggested detection threshold: **~92 ADC units**
- Two-sample t-test: p << 0.001 (highly significant)

---

## Files

```
tests/
├── analysis/            ← run Octave from here
│   ├── nira_analysis.m
│   ├── nira_plot_*.m
│   ├── clean_water.csv
│   └── micro_water.csv
└── results/             ← auto-created, PNGs saved here
```

---

## How to Run

### Requirements
- [GNU Octave](https://octave.org/) ≥ 7.x  
  On Debian/Ubuntu: `sudo apt install octave`

```bash
cd tests/analysis
octave nira_analysis.m
```

Plots are saved to `tests/results/`.

---

## Preparing CSVs from InfluxDB Export

The raw InfluxDB annotated CSVs have 3 header rows. Convert them once with Python:

```python
import pandas as pd

for name, fname in [('clean_water', 'test-0_cleanWater.csv'),
                    ('micro_water',  'test-1_water_with_microplastics.csv')]:
    df = pd.read_csv(fname, skiprows=3)
    piv = df.pivot_table(index='_time', columns='_field',
                         values='_value', aggfunc='first').astype(float)
    piv.reset_index().to_csv(f'{name}.csv', index=False)
    print(f'Saved {name}.csv')
```

---

*Part of [Project Nira](https://github.com/only-foss/Project-Nira) — FOSS microplastic detection sensor.*
