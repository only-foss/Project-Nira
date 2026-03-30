# Firmware Setup

The v1.5 ESP32 firmware includes multiple robustness upgrades for FOSS Hack 2026.

## Major Features
1. **Local InfluxDB Integration**: Fully open-source compliant logging (`http://192.168.1.100:8086`).
2. **Internal Temperature Compensation**: A linear drift algorithm eliminates standard environmental variance (`comp_diff = diff - (temp_c - 25.0) * 8.5`).

## Flashing Instructions
1. Open `firmware/v1.5_esp32_fdc1004/Project-Nira` in PlatformIO or Arduino IDE.
2. Fill in your `WIFI_SSID` and `WIFI_PASS`.
3. Set your target `INFLUXDB_URL` (IP of your local self-hosted instance).
4. Flash to the ESP32 DevKit module.
