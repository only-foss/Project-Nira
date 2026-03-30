# Hardware Design

The Nira v1.5 hardware is based on an ESP32 microcontroller and a Texas Instruments FDC1004 capacitance-to-digital converter.

## Components
- **ESP32 DevKit v1**: Core processor and WiFi/SD-card interface.
- **FDC1004**: Measures differential capacitance across electrodes.
- **MicroSD Module**: Used for offline data logging.
- **DS18B20**: Temperature sensor used for drift compensation.

## KiCad Project
The hardware source files are located in `hardware/v1.5_esp32_sensor/`.
To build the sensor:
1. Open the project in KiCad 7+.
2. Ensure the ESP32, FDC1004, and SD card modules are wired according to the schematic.
3. Keep electrode traces (CIN1, CIN4) as short as possible to reduce parasitic capacitance!
