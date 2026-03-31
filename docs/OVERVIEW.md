# Technical Project Report: Project Nira

### 1. Executive Summary
Project Nira is an open-hardware initiative to develop an affordable system for detecting microplastics in water. By utilizing **capacitance-based sensing**, the project aims to move microplastic testing from the laboratory to the field.

### 2. Introduction & Motivation
Environmental monitoring tools are often proprietary and expensive. Project Nira was born from the need for local communities to respond effectively to pollution by measuring the problem locally. The goal is to enable schools and citizen scientists to test water independently.

### 3. System Architecture
The architecture focuses on **signal behavior and noise handling** within an impedance sensing framework.
*   **Hardware:** A scalable layout using the ESP32 and FDC1004.
*   **Sensing:** Uses differential capacitance to identify permittivity shifts caused by microplastic particles.
*   **Data Pipeline:** Real-time data transmission from the sensor node to a cloud-based InfluxDB instance, or local logging via dashboard.

### 4. Implementation Status
The project is currently in the **v1.5 prototype phase**. Key focuses include:
*   Developing the differential sensing architecture.
*   Designing a scalable hardware layout (breadboard validated, PCB planned).
*   Studying signal behavior to reduce environmental noise via data analytics.

### 5. Conclusion & Future Work
In the long term, Project Nira aims to contribute to **open environmental data**. Future work involves refining the hardware layout for mass reproducibility and improving the sensitivity of the differential capacitance sensors to detect even smaller particles.
