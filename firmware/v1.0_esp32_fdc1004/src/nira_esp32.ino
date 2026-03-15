/**
 * NIRA v1.0.2 - Micro-plastic Detection Capacitive Flow Sensor
 * ESP32 + ProtoCentral FDC1004 (CH1 + CH4 sampling)
 *
 * Features (manual update 15-Mar-2026):
 * • 100 Hz sampling rate
 * • CH1 (library ch 0 / CIN1) and CH4 (library ch 3 / CIN4) measured back-to-back
 * • Common GND plate for both channels
 * • CSV output: time_ms,CH1_raw,CH4_raw,Diff_C1_C4,delta_us   ← now plots difference!
 * • WiFi + ThingSpeak live dashboard (CH1, CH4 + Diff_C1_C4)
 *
 * License: MIT
 * Hardware license reference: CERN OHL-S v2 (for associated KiCad files)
 * IoT addition: fully open-source compliant
 */
#include <Wire.h>
#include <Protocentral_FDC1004.h>
#include <WiFi.h>
#include <ThingSpeak.h>

// ============================================================================
// HARDWARE PINS & CONFIG
static const uint8_t SDA_PIN = 21;
static const uint8_t SCL_PIN = 22;
static const uint16_t SAMPLE_INTERVAL_MS = 10; // 100 Hz

// FDC1004 channels - UPDATED FOR YOUR NEW WIRING
static const uint8_t CH1_CIN = 0; // C1 - library channel 0 (CIN1 pin)
static const uint8_t CH4_CIN = 3; // C4 - library channel 3 (CIN4 pin)

FDC1004 fdc_sensor(&Wire, FDC1004_RATE_100HZ);

// ============================================================================
// THINGSPEAK + WIFI CONFIG - CHANGE THESE
const char* WIFI_SSID         = "MI";           // ← change
const char* WIFI_PASS         = "wasd1234";       // ← change
unsigned long THINGSPEAK_CHANNEL = 3300652;                 // ← your channel ID
const char* THINGSPEAK_KEY    = "1XRHLD2A716K76WM";       // ← paste from ThingSpeak

WiFiClient client;

// ============================================================================
// GLOBALS
static uint32_t lastUpload      = 0;
static uint32_t lastWiFiCheck   = 0;

// ============================================================================
// SETUP
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
  Serial.println("time_ms,CH1_raw,CH4_raw,Diff_C1_C4,delta_us");
  Serial.println("Sensor ready – 100 Hz C1+C4 sampling + live difference");

  // WiFi + ThingSpeak
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());

  ThingSpeak.begin(client);
  Serial.println("ThingSpeak ready – CH1, CH4 + Diff_C1_C4 every 15 s");
}

// ============================================================================
// LOOP - SERIAL CSV STILL WORKS EXACTLY FOR PLOTTING
void loop() {
  static uint32_t last_sample = 0;
  uint32_t now = millis();

  if (now - last_sample >= SAMPLE_INTERVAL_MS) {
    last_sample = now;
    uint32_t t1 = micros();
    uint16_t ch1_raw = read_channel(CH1_CIN);
    uint16_t ch4_raw = read_channel(CH4_CIN);
    uint32_t delta_us = micros() - t1;

    // Difference C1 - C4 (raw, signed - exactly what you asked)
    float diff = (float)ch1_raw - ch4_raw;

    // === YOUR SERIAL OUTPUT - NOW WITH DIFFERENCE FOR PLOTTER ===
    Serial.print(now);
    Serial.print(',');
    Serial.print(ch1_raw);
    Serial.print(',');
    Serial.print(ch4_raw);
    Serial.print(',');
    Serial.print(diff);
    Serial.print(',');
    Serial.println(delta_us);

    // ThingSpeak upload every 15 s
    if (now - lastUpload >= 15000UL) {
      lastUpload = now;
      send_to_thingspeak(ch1_raw, ch4_raw, diff);
    }
  }

  // WiFi auto-reconnect
  if (now - lastWiFiCheck >= 30000UL) {
    lastWiFiCheck = now;
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi dropped - reconnecting...");
      WiFi.reconnect();
    }
  }
}

// ============================================================================
// THINGSPEAK FUNCTION - NOW WITH LIVE DIFFERENCE
void send_to_thingspeak(uint16_t ch1, uint16_t ch4, float diff) {
  if (WiFi.status() != WL_CONNECTED) return;

  ThingSpeak.setField(1, ch1);
  ThingSpeak.setField(2, ch4);
  ThingSpeak.setField(3, diff);          // ← live Diff_C1_C4 graph

  int code = ThingSpeak.writeFields(THINGSPEAK_CHANNEL, THINGSPEAK_KEY);

  if (code == 200) {
    Serial.println("✅ ThingSpeak: CH1 + CH4 + Diff uploaded");
  } else {
    Serial.println("⚠️ ThingSpeak error: " + String(code));
  }
}

// ============================================================================
// ORIGINAL FUNCTIONS (only wiring text updated)
void print_banner() {
  Serial.println();
  Serial.println("=======================================");
  Serial.println(" NIRA v2.3 – C1 + C4 Flow Sensor ");
  Serial.println(" ESP32 + FDC1004 @ 100 Hz + Live Diff ");
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
  Serial.println("VCC → 3V3 | GND → GND");
  Serial.println("SDA → GPIO21 | SCL → GPIO22");
  Serial.println("CIN1 (C1) → Electrode 1");
  Serial.println("CIN4 (C4) → Electrode 2");
  Serial.println("Common GND plate required");
  Serial.println("=============================");
}
