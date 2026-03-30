# Usage Guide — Project Nira v1.5

This guide details the setup and operation of the Project-Nira microplastics detection system.

---

### Hardware Setup

![Project Nira Circuit Diagram](../assets/Circuit-Conenction-Diagram-drawio.png)

1. **Sensor Placement:** Position the two copper electrodes along the water flow path.
2. **FDC1004 Connection:** Connect the electrodes to the ProtoCentral FDC1004 inputs **CIN1 (CH1)** and **CIN4 (CH4)**.
3. **Microcontroller Wiring:** Connect the FDC1004 to the **ESP32** via the I2C interface:
    - **SCL** → ESP32 GPIO 22
    - **SDA** → ESP32 GPIO 21
    - **VCC/GND** → 3.3V power source
    - Add 4.7kΩ pull-up resistors on SDA and SCL.

---

### Software Configuration
1. **Firmware:** Open `firmware/v1.5_esp32_fdc1004/Project-Nira` in PlatformIO or Arduino IDE.
2. **Edit credentials** in `main.cpp`:
    - `WIFI_SSID` / `WIFI_PASS`
    - `INFLUXDB_URL`, `TOKEN`, `ORG`, and `BUCKET` (for your local FOSS InfluxDB instance).
3. **Flash** the code to the ESP32.

---

### Operation Options

#### Option A — Desktop GUI Dashboard (Recommended, no WiFi required)
The Python dashboard allows you to view live capacitance plots, tweak parameters, and record to CSV locally over USB context.

```bash
# Launch the desktop UI
python python/nira_dashboard.py

# OR launch in headless CLI mode logging to a specific file:
python python/nira_dashboard.py --cli --port /dev/ttyUSB0 --baud 115200 --out my_data.csv
```

#### Option B — InfluxDB + Grafana Dashboard
1. Run clean water through the sensor to establish a baseline.
2. Monitor your local **InfluxDB** dashboard in real-time.
3. Export data with: `python python/nira-reader.py --start -1h --label my_sample`

---

### Data Analysis
```bash
cd tests/analysis/
octave nira_analysis.m
```
Results saved to `tests/results/` as PNG plots.

---

### Known Limitations (v1.5)
- Temperature compensation uses a fixed 25°C placeholder. Connect a DS18B20 sensor for real field compensation (planned: v1.6).
- SD card offline logging is planned for v1.6; use `serial_logger.py` in the meantime.
- PCB layout not yet available; use the breadboard wiring guide in `hardware/v1.5_esp32_sensor/breadboard/WIRING_NOTES.md`.
