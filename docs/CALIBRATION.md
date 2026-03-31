# Project Nira — Calibration & Zeroing Guide

## Why Calibration Matters

Project Nira measures *differential* capacitance. The absolute pF value
depends on electrode geometry, water conductivity, and temperature.
Only the *change from baseline* (`d0`–`d3`, `mp_index`) is meaningful.

## Baseline Capture Procedure

1. Fill sensor chamber with **clean, particle-free water** (distilled preferred)
2. Submerge electrodes fully — no air bubbles
3. Wait **30 seconds** for thermal and electrical stabilisation
4. Click **ZERO / BASELINE** in the GUI (or send `CMD:ZERO` via serial)
5. Firmware averages 32 readings per channel (~640 ms at 100 S/s)
6. GUI log shows: `zero_done base_pF: [xx.xx, xx.xx, xx.xx, xx.xx]`
7. All subsequent `d0`–`d3` and `mp_index` values are relative to this

## When to Re-Zero

- At the start of every measurement session
- After moving to a different water source
- After temperature change >5°C
- After device power cycle
- After replacing or repositioning electrodes

## Interpreting mp_index

| mp_index (pF RMS) | Interpretation |
|-------------------|----------------|
| < 0.05 | Baseline noise — clean water |
| 0.05 – 0.10 | Slight perturbation — low particle count |
| > 0.10 | **Alert** — significant capacitive shift |
| > 0.30 | High particle load — verify with lab method |

These thresholds are empirical. Calibrate against known microplastic
concentrations for your specific electrode geometry and water chemistry.

## Field Notes

- Temperature coefficient: ~0.02 pF/°C — always re-zero after temp changes
- Bubbles on electrodes are the most common source of false positives
- 316L stainless is resistant to corrosion but wipe electrodes between samples
