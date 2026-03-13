/**
 * NIRA v2.0 - Micro-plastic Detection Capacitive Flow Sensor
 * ESP32 + ProtoCentral FDC1004 (C1 + C2 near-simultaneous sampling)
 * 
 * Features:
 * • 100 Hz sampling rate
 * • CIN1 (C1) and CIN2 (C2) measured back-to-back (<500 µs apart)
 * • Common GND plate for both channels
 * • CSV output: time_ms, CH1_raw, CH2_raw, delta_us
 * 
 * License: MIT
 * Hardware license reference: CERN OHL-S v2 (for associated KiCad files)
 */

#include <Wire.h>
#include <Protocentral_FDC1004.h>

// ============================================================================
// HARDWARE PINS & CONFIG
static const uint8_t SDA_PIN          = 21;
static const uint8_t SCL_PIN          = 22;
static const uint16_t SAMPLE_INTERVAL_MS = 10;   // 100 Hz

// FDC1004 channels (CIN0 = channel 1, CIN1 = channel 2, common GND)
static const uint8_t CH1_CIN          = 0;       // CIN0
static const uint8_t CH2_CIN          = 1;       // CIN1

FDC1004 fdc_sensor(&Wire, FDC1004_RATE_100HZ);

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  delay(1500);

  print_banner();

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000UL);

  if (!init_sensor()) {
    print_wiring_error();
    while (true) delay(1000);
  }

  Serial.println("time_ms,CH1_raw,CH2_raw,delta_us");
  Serial.println("Sensor ready – 100 Hz dual-channel sampling");
}

void loop() {
  static uint32_t last_sample = 0;
  uint32_t now = millis();

  if (now - last_sample >= SAMPLE_INTERVAL_MS) {
    last_sample = now;

    uint32_t t1 = micros();
    uint16_t ch1_raw = read_channel(CH1_CIN);
    uint16_t ch2_raw = read_channel(CH2_CIN);
    uint32_t delta_us = micros() - t1;

    Serial.print(now);
    Serial.print(',');
    Serial.print(ch1_raw);
    Serial.print(',');
    Serial.print(ch2_raw);
    Serial.print(',');
    Serial.println(delta_us);
  }
}

// ============================================================================
// FUNCTIONS
// ============================================================================

void print_banner() {
  Serial.println();
  Serial.println("=======================================");
  Serial.println("   NIRA v2.0 – Capacitive Flow Sensor  ");
  Serial.println("   ESP32 + FDC1004 @ 100 Hz           ");
  Serial.println("=======================================");
}

bool init_sensor() {
  Serial.print("FDC1004 initialization... ");
  if (!fdc_sensor.begin()) {
    Serial.println("FAILED");
    return false;
  }
  Serial.println("OK");
  return true;
}

uint16_t read_channel(uint8_t ch) {
  return fdc_sensor.getCapacitance(ch);
}

void print_wiring_error() {
  Serial.println("\n=== WIRING / CONFIG ERROR ===");
  Serial.println("FDC1004 → ESP32");
  Serial.println("VCC    → 3V3");
  Serial.println("GND    → GND");
  Serial.println("SDA    → GPIO21");
  Serial.println("SCL    → GPIO22");
  Serial.println("CIN1   → Electrode 1");
  Serial.println("CIN2   → Electrode 2");
  Serial.println("Common GND plate required");
  Serial.println("=============================");
}