// SPDX-License-Identifier: MIT
/**
 * NIRA v1.2.6- Micro-plastic Detection Capacitive Flow Sensor
 * ESP32 + ProtoCentral FDC1004 (C1 + C4 near-simultaneous sampling)
 *
 * Features:
 * • 100 Hz sampling rate
 * • C1 (library ch 0) and C4 (library ch 3)
 * • CSV output for Serial Plotter: time_ms,CH1_raw,CH4_raw,Diff_C1_C4,delta_us
 * • InfluxDB Cloud v2 + Grafana live dashboards
 *
 * License: MIT
 * Hardware license: CERN OHL-S v2
 */

#include <Arduino.h>
#include <Wire.h>
#include <Protocentral_FDC1004.h>
#include <WiFiMulti.h>
#include <InfluxDbClient.h>
#include <InfluxDbCloud.h>

// ============================================================================
// HARDWARE PINS & CONFIG
static const uint8_t SDA_PIN = 21;
static const uint8_t SCL_PIN = 22;
static const uint16_t SAMPLE_INTERVAL_MS = 10; // 100 Hz

// FDC1004 channels
static const uint8_t CH1_CIN = 0;  // C1
static const uint8_t CH4_CIN = 3;  // C4

FDC1004 fdc_sensor(&Wire, FDC1004_RATE_100HZ);

// ============================================================================
// WIFI + INFLUXDB CLOUD CONFIG
const char* WIFI_SSID         = "YOUR SSID";
const char* WIFI_PASS         = "YOUR PASSWORD";

// InfluxDB Cloud (free tier)
#define INFLUXDB_URL          "INFLUXDB_URL"        // Your InfluxDB cloud link
#define INFLUXDB_TOKEN        "TOCKEN"              // Your Tocken
#define INFLUXDB_ORG          "ORG"                 // Your Bucket
#define INFLUXDB_BUCKET       "BUCKET"
#define TZ_INFO               "Asia/Kolkata"        // Your Time Zone

WiFiMulti wifiMulti;
InfluxDBClient client(INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_TOKEN, InfluxDbCloud2CACert);
Point sensorData("nira_sensor");

// ============================================================================
// GLOBALS
static uint32_t lastUpload    = 0;
static uint32_t lastWiFiCheck = 0;

// ============================================================================
// HELPER FUNCTION
void print_banner();
bool init_sensor();
uint16_t read_channel(uint8_t ch);
void print_wiring_error();
void send_to_influxdb(uint16_t ch1, uint16_t ch4, float diff);

// ============================================================================
// SETUP
void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  delay(1500);

  print_banner();

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000UL);

  if (!init_sensor()) {
    print_wiring_error();
    while (true) delay(1000);
  }

  Serial.println("time_ms,CH1_raw,CH4_raw,Diff_C1_C4,delta_us");
  Serial.println("Sensor ready 100 Hz sampling + InfluxDB ");

  // WiFi
  wifiMulti.addAP(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  while (wifiMulti.run() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());

  // Time sync for InfluxDB
  timeSync(TZ_INFO, "pool.ntp.org", "time.nis.gov");

  // Add tags
  sensorData.addTag("device", "nira_esp32");
  sensorData.addTag("team", "domination");

  if (client.validateConnection()) {
    Serial.println("Connected to InfluxDB Cloud");
  } else {
    Serial.println("InfluxDB connection failed");
  }

  Serial.println("Ready – uploading every 15 s to InfluxDB");
}

// ============================================================================
// LOOP
void loop() {
  static uint32_t last_sample = 0;
  uint32_t now = millis();

  if (now - last_sample >= SAMPLE_INTERVAL_MS) {
    last_sample = now;

    uint32_t t1 = micros();
    uint16_t ch1_raw = read_channel(CH1_CIN);
    uint16_t ch4_raw = read_channel(CH4_CIN);
    uint32_t delta_us = micros() - t1;

    float diff = (float)ch1_raw - ch4_raw;

    // Serial Plotter output
    Serial.print(now);
    Serial.print(',');
    Serial.print(ch1_raw);
    Serial.print(',');
    Serial.print(ch4_raw);
    Serial.print(',');
    Serial.print(diff);
    Serial.print(',');
    Serial.println(delta_us);

    // Upload every 1 s
    if (now - lastUpload >= 1000UL) {
      lastUpload = now;
      send_to_influxdb(ch1_raw, ch4_raw, diff);
    }
  }

  // WiFi reconnect
  if (now - lastWiFiCheck >= 30000UL) {
    lastWiFiCheck = now;
    if (wifiMulti.run() != WL_CONNECTED) {
      Serial.println("WiFi dropped - reconnecting...");
    }
  }
}

// ============================================================================
// INFLUXDB WRITE
void send_to_influxdb(uint16_t ch1, uint16_t ch4, float diff) {
  if (wifiMulti.run() != WL_CONNECTED) return;

  sensorData.clearFields();
  sensorData.addField("ch1_raw", ch1);
  sensorData.addField("ch4_raw", ch4);
  sensorData.addField("diff_c1_c4", diff);

  if (!client.writePoint(sensorData)) {
    Serial.print("InfluxDB write failed: ");
    Serial.println(client.getLastErrorMessage());
  } else {
    Serial.println("Data written to InfluxDB");
  }
}

// ============================================================================
// HELPER FUNCTIONS
void print_banner() {
  Serial.println();
  Serial.println("=======================================");
  Serial.println(" NIRA v2.5 C1 + C4 Flow Sensor ");
  Serial.println(" ESP32 + FDC1004 + InfluxDB ");
  Serial.println("=======================================");
}

bool init_sensor() {
  Serial.print("FDC1004 initialization... ");
  bool ok = fdc_sensor.begin();
  Serial.println(ok ? "OK" : "FAILED");
  return ok;
}

uint16_t read_channel(uint8_t ch) {
  return fdc_sensor.getCapacitance(ch);
}

void print_wiring_error() {
  Serial.println("\n=== WIRING ERROR ===");
  Serial.println("FDC1004 → ESP32");
  Serial.println("VCC → 3V3 | GND → GND");
  Serial.println("SDA → GPIO21 | SCL → GPIO22");
  Serial.println("CIN1 (C1) → Electrode 1");
  Serial.println("CIN4 (C4) → Electrode 2");
  Serial.println("Common GND plate required");
  Serial.println("=============================");
}
