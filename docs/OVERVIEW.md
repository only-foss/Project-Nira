

# Technical Project Report: Project-Nira

### 1. Executive Summary
Project-Nira is an open-hardware initiative to develop an affordable system for detecting micro-plastics in water. By utilizing **impedance-based sensing**, the project aims to move micro-plastic testing from the laboratory to the field.

### 2. Introduction & Motivation
Environmental monitoring tools are often proprietary and expensive. Project-Nira was born from the need for local communities to respond effectively to pollution by measuring the problem locally. The goal is to enable schools and citizen scientists to test water independently.

### 3. System Architecture
The architecture focuses on **signal behavior and noise handling** within an impedance sensing framework.
*   **Hardware:** A scalable layout using the ESP32 and FDC1004.
*   **Sensing:** Uses differential capacitance to identify permittivity shifts caused by micro-plastic particles.
*   **Data Pipeline:** Real-time data transmission from the sensor node to a cloud-based InfluxDB instance.

### 4. Implementation Status
The project is currently in the **research and design phase**. Key focuses include:
*   Developing the impedance sensing architecture.
*   Designing a scalable hardware layout.
*   Studying signal behavior to reduce environmental noise.

### 5. Conclusion & Future Work
In the long term, Project-Nira aims to contribute to **open environmental data**. Future work involves refining the hardware layout for mass reproducibility and improving the sensitivity of the differential capacitance sensors to detect even smaller particles.
```
