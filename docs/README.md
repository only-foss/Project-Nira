# Project-Nira: Real-Time Micro-plastic Detection

**Project-Nira** is an **Open Source Hardware (OSHW)** initiative designed to quantify micro-plastics present in water in real-time using a flow-through method.


### The Problem
Micro-plastics (particles smaller than 5 mm) are now found in rivers, lakes, and drinking water. Currently, detection requires advanced spectroscopy, complex lab preparation, and trained specialists. These systems often cost over **₹10 lakh**, making regular monitoring impossible for schools and rural communities.

### The Solution
Project-Nira provides a **low-cost, portable, and repairable** alternative built from easily available components. It uses **impedance-based sensing** (specifically differential capacitance) to detect suspended micro-plastic particles without expensive laboratory setups.


### Technical Overview
The system leverages permittivity changes to detect pollutants.
*   **Microcontroller:** ESP32 (handles logic and Wi-Fi connectivity).
*   **Sensor Interface:** ProtoCentral FDC1004 (Capacitance-to-Digital Converter).
*   **Detection Method:** **Differential Capacitance Mode** using two sensors (**C1 and C2**).
*   **Theory:** Plastic has a different permittivity than water; its presence in the flow path alters the capacitance read by the FDC1004.
*   **Cloud Logging:** Data is pushed from the ESP32 to **InfluxDB** for real-time monitoring.

### Open Source Commitment
All designs, firmware, and documentation are released openly to enable **decentralized environmental monitoring**.
