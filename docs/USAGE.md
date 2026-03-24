
# Usage Guide for Project-Nira

This guide details the setup and operation of the Project-Nira micro-plastic detection system.

### Hardware Setup
1.  **Sensor Placement:** Position your differential capacitance sensors (C1 and C2) along the water flow path.
2.  **FDC1004 Connection:** Connect the sensors to the ProtoCentral FDC1004 inputs.
3.  **Microcontroller Wiring:** Connect the FDC1004 to the **ESP32** via the I2C interface:
    *   **SCL** -> ESP32 GPIO 22 (default)
    *   **SDA** -> ESP32 GPIO 21 (default)
    *   **VCC/GND** -> 3.3V power source.

### Software Configuration
1.  **Firmware:** Open the project firmware in the Arduino IDE or VS Code (PlatformIO).
2.  **Environment Variables:** Update the following in your configuration file:
    *   `WIFI_SSID` / `WIFI_PASSWORD`
    *   `INFLUXDB_URL`, `TOKEN`, `ORG`, and `BUCKET`.
3.  **Upload:** Flash the code to the ESP32.

### Operation
1.  **Baseline Calibration:** Run clean water through the sensor to establish a baseline capacitance reading.
2.  **Real-Time Monitoring:** As water flows, monitor your **InfluxDB dashboard**.
3.  **Data Analysis:** Use the logged data to calculate the concentration of particles over time.
