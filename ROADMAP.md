# Project Nira — Field Deployment Ready Roadmap

**Version:** 1.0 (26 March 2026)  
**Status:** Addressing judge feedback from Open Check-in  
**Goal:** Make Nira truly field-deployable for rural water monitoring (offline, low-power, remote sensing)

## 1. Current State Assessment (Re-assessed 26 Mar 2026)

**Strengths:**
- Differential capacitance sensing (C1-C4)
- InfluxDB Cloud integration
- OSHW approach

**Critical Gaps (Judge Feedback):**
- No temperature compensation → significant reading drift in field conditions
- No offline logging → data loss when WiFi/Internet is unavailable
- Firmware mismatch between branches (PlatformIO migration incomplete)
- No waterproof mechanical enclosure
- No ML-based detection model


## 2. Phase 0: Immediate Fixes (27–28 March)

- [x] Merge `feature/platformio-migration` branch into `main`
- [x] Add temperature compensation (ESP32 built-in sensor + DS18B20 option)
- [x] Implement offline SD card logging with fallback
- [x] Update README.md — remove over-promising statements and add honest status
- [ ] Record and upload 3-minute pure demo video (showing live + offline mode)

## 3. Phase 1: V1 Field-Ready (29–31 March)

### Temperature Compensation
- Use ESP32 internal temperature sensor for basic correction
- Add DS18B20 external sensor support (GPIO 4)
- Apply linear compensation: `compensated_diff = diff - (temp - 25.0) * 8.5`

### Offline Logging + RTC
- Add microSD card logging (CSV format)
- Add DS3231 RTC for accurate timestamps during offline operation
- Log format: `timestamp, ch1_raw, ch4_raw, diff, temperature, status`

### Mechanical Enclosure (V1)
- Design IP67-rated 3D-printable waterproof enclosure
- Include flow cell with quick-connect fittings
- Add mounting for solar panel + 18650 battery

## 4. Phase 2: V2 — Low Power Remote Sensing (1–10 April)

**Hardware Migration:** STM32 Bluepill (STM32F103C8) as primary controller

**Key Improvements:**
- Ultra-low power consumption (deep sleep ~10µA)
- Native LoRa / LoRaWAN support for remote areas
- Better RTC and timer support
- Same FDC1004 sensor + DS18B20

**V2 Features:**
- LoRaWAN connectivity (TTN/Helium)
- Deep sleep with RTC wake-up
- SD card + external flash buffering
- Solar + battery powered system

**Firmware:** Rewrite using STM32CubeIDE / PlatformIO / STM32duino

## 5. Data Cleaning + ML Model (Parallel Track)

**Steps:**
1. Data cleaning pipeline (remove outliers, temperature normalization)
2. Feature engineering (`diff`, `|diff|`, `ch1/ch4 ratio`, temperature)
3. Train binary classifier (Random Forest / LightGBM)
4. Export model for embedded inference (`.tflite` or C array)

**Folder Structure:**

---
├── data_cleaning.ipynb
├── feature_engineering.py
├── model_training.py
└── model_export/
---

## 6. Full Field Deployment Checklist (Target: May 2026)

- [ ] Temperature compensated sensing
- [ ] Offline SD + RTC logging
- [ ] IP67 waterproof enclosure + flow cell
- [ ] Low-power V2 hardware (STM32 + LoRaWAN)
- [ ] On-device ML inference
- [ ] Solar + battery power system
- [ ] Remote data transmission & dashboard
- [ ] Real field test report (river/lake data)

## 7. Timeline

- **27–28 Mar:** Phase 0 (Temperature + Offline + README fix)
- **29–31 Mar:** Phase 1 (Enclosure design + demo video)
- **1–10 Apr:** Phase 2 (STM32 Bluepill + LoRa V2)
- **11–20 Apr:** ML model training + embedded deployment
- **May 2026:** First real-world field deployment

---

**Next Immediate Action:**
Create this file as `ROADMAP.md` in the repository root and start with **Phase 0**.

This roadmap directly addresses the judge’s feedback and demonstrates clear vision for shifting Nira field-ready.