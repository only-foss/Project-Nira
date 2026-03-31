// SPDX-License-Identifier: MIT
/**
 * @file main.cpp
 * @brief Project Nira — ESP32-S3 Firmware v1.1
 *
 * Reads capacitance/impedance data from the FDC1004 (or ADS131M08 ADC) and
 * streams structured JSON lines over USB-Serial at 115200 baud.
 *
 * Serial output protocol (one JSON object per line, newline-terminated):
 *   {"ts":1234567,"ch0":12.34,"ch1":12.10,"ch2":11.98,"ch3":12.05,
 *    "temp":28.5,"bat_mv":3820,"mode":"sample","mp_index":0.042}
 *
 * Control commands received over Serial (newline-terminated):
 *   CMD:ZERO          — re-zero / baseline capture
 *   CMD:START         — start streaming
 *   CMD:STOP          — pause streaming
 *   CMD:RATE:<n>      — set sample interval in ms (e.g. CMD:RATE:500)
 *   CMD:RESET         — software reset
 *
 * Hardware:
 *   ESP32-S3 + FDC1004 (I2C) + optional ADS131M08 (SPI)
 *   316L stainless electrodes, IP67 enclosure
 *
 * License: MIT
 * Project: https://github.com/only-foss/Project-Nira
 */

#include <Arduino.h>
#include <Wire.h>
#include <ArduinoJson.h>   // ArduinoJson v7 — add to platformio.ini: bblanchon/ArduinoJson

// ─── FDC1004 Register Map ────────────────────────────────────────────────────
#define FDC1004_ADDR        0x50
#define FDC1004_FDC_CONF    0x0C
#define FDC1004_MEAS1_MSB   0x00
#define FDC1004_MEAS2_MSB   0x02
#define FDC1004_MEAS3_MSB   0x04
#define FDC1004_MEAS4_MSB   0x06
#define FDC1004_CONF_CH1    0x08
#define FDC1004_CONF_CH2    0x09
#define FDC1004_CONF_CH3    0x0A
#define FDC1004_CONF_CH4    0x0B
#define FDC_CAP_DAC_DISABLED 0x1C00  // CAPDAC = 0, CHA = CHx, CHB = CAPDAC

// ─── Pin Definitions ─────────────────────────────────────────────────────────
#define I2C_SDA_PIN         21
#define I2C_SCL_PIN         22
#define LED_STATUS_PIN      2    // onboard LED
#define BAT_ADC_PIN         34   // battery voltage divider (adjust for your HW)

// ─── Configuration ───────────────────────────────────────────────────────────
#define SERIAL_BAUD         115200
#define DEFAULT_SAMPLE_MS   500   // default sample interval
#define BASELINE_SAMPLES    32    // samples averaged for zero baseline

// ─── Globals ─────────────────────────────────────────────────────────────────
static float   baseline_pF[4]  = {0.0f, 0.0f, 0.0f, 0.0f};
static bool    streaming        = true;
static uint32_t sample_interval = DEFAULT_SAMPLE_MS;
static uint32_t last_sample_ms  = 0;
static uint32_t sample_count    = 0;

// ─── FDC1004 Helpers ─────────────────────────────────────────────────────────

/**
 * @brief Write a 16-bit value to an FDC1004 register.
 */
static bool fdc_write16(uint8_t reg, uint16_t val) {
    Wire.beginTransmission(FDC1004_ADDR);
    Wire.write(reg);
    Wire.write((val >> 8) & 0xFF);
    Wire.write(val & 0xFF);
    return Wire.endTransmission() == 0;
}

/**
 * @brief Read a 32-bit measurement result from the FDC1004 (MSB + LSB regs).
 */
static int32_t fdc_read_meas(uint8_t msb_reg) {
    Wire.beginTransmission(FDC1004_ADDR);
    Wire.write(msb_reg);
    if (Wire.endTransmission(false) != 0) return 0;

    Wire.requestFrom((uint8_t)FDC1004_ADDR, (uint8_t)4);
    if (Wire.available() < 4) return 0;

    int32_t raw = ((int32_t)Wire.read() << 24)
                | ((int32_t)Wire.read() << 16)
                | ((int32_t)Wire.read() <<  8)
                |  (int32_t)Wire.read();
    return raw >> 8;  // 24-bit signed result
}

/**
 * @brief Convert raw FDC1004 24-bit signed value to picofarads.
 *        Full-scale = ±15 pF, 24-bit signed: 1 LSB = 30 pF / 2^24
 */
static float raw_to_pF(int32_t raw) {
    return (float)raw * (30.0f / (float)(1 << 24));
}

/**
 * @brief Configure all 4 FDC1004 channels for single-ended measurement.
 */
static void fdc_configure() {
    // MEAS1..4: CHA = CH1..4, CHB = CAPDAC, CAPDAC = 0
    fdc_write16(FDC1004_CONF_CH1, (0x00 << 13) | FDC_CAP_DAC_DISABLED);
    fdc_write16(FDC1004_CONF_CH2, (0x01 << 13) | FDC_CAP_DAC_DISABLED);
    fdc_write16(FDC1004_CONF_CH3, (0x02 << 13) | FDC_CAP_DAC_DISABLED);
    fdc_write16(FDC1004_CONF_CH4, (0x03 << 13) | FDC_CAP_DAC_DISABLED);
    // FDC_CONF: RATE=100S/s (01), REPEAT=1, MEAS1..4 enable
    fdc_write16(FDC1004_FDC_CONF, 0x0F9F);
    delay(20);
}

/**
 * @brief Trigger a single measurement cycle and read all 4 channels.
 * @param[out] pF  Array of 4 floats (pF per channel)
 */
static bool fdc_read_all(float pF[4]) {
    // Trigger single shot
    fdc_write16(FDC1004_FDC_CONF, 0x8F9F);
    delay(25);  // wait for conversion (100 S/s → ~10 ms, add margin)

    const uint8_t msb_regs[4] = {
        FDC1004_MEAS1_MSB, FDC1004_MEAS2_MSB,
        FDC1004_MEAS3_MSB, FDC1004_MEAS4_MSB
    };
    for (int i = 0; i < 4; i++) {
        int32_t raw = fdc_read_meas(msb_regs[i]);
        pF[i] = raw_to_pF(raw);
    }
    return true;
}

// ─── Sensor Utilities ────────────────────────────────────────────────────────

/**
 * @brief Read battery voltage in millivolts via ADC.
 *        Assumes 1:2 voltage divider, 3.3 V ref, 12-bit ADC.
 */
static uint32_t read_bat_mv() {
    uint32_t adc = analogRead(BAT_ADC_PIN);
    // (adc / 4095) * 3300 mV * 2 (divider)
    return (adc * 6600UL) / 4095UL;
}

/**
 * @brief Read die temperature from ESP32 internal sensor (approximate).
 */
static float read_temp_c() {
    // ESP32 has temperatureRead() in some frameworks; fallback to NaN
#ifdef __XTENSA__
    extern float temperatureRead();
    return temperatureRead();
#else
    return NAN;
#endif
}

/**
 * @brief Microplastic index: mean differential capacitance from baseline.
 *        Higher deviation → higher particle count proxy.
 */
static float compute_mp_index(float pF[4]) {
    float sum = 0.0f;
    for (int i = 0; i < 4; i++) {
        float delta = pF[i] - baseline_pF[i];
        sum += delta * delta;
    }
    // RMS deviation in pF
    return sqrtf(sum / 4.0f);
}

// ─── Baseline (Zero) Capture ─────────────────────────────────────────────────

/**
 * @brief Capture baseline by averaging BASELINE_SAMPLES readings.
 *        Called on startup and whenever CMD:ZERO is received.
 */
static void capture_baseline() {
    float accum[4] = {0};
    Serial.println("{\"status\":\"zeroing\"}");
    for (int s = 0; s < BASELINE_SAMPLES; s++) {
        float pF[4];
        if (fdc_read_all(pF)) {
            for (int i = 0; i < 4; i++) accum[i] += pF[i];
        }
        delay(20);
    }
    for (int i = 0; i < 4; i++) {
        baseline_pF[i] = accum[i] / BASELINE_SAMPLES;
    }
    Serial.printf("{\"status\":\"zero_done\","
                  "\"base_pF\":[%.4f,%.4f,%.4f,%.4f]}\n",
                  baseline_pF[0], baseline_pF[1],
                  baseline_pF[2], baseline_pF[3]);
}

// ─── Command Parser ───────────────────────────────────────────────────────────

/**
 * @brief Parse and execute a command string received over Serial.
 * @param cmd  Null-terminated command string (leading/trailing whitespace OK).
 */
static void handle_command(const char* cmd) {
    if (strncmp(cmd, "CMD:ZERO", 8) == 0) {
        capture_baseline();
    } else if (strncmp(cmd, "CMD:START", 9) == 0) {
        streaming = true;
        Serial.println("{\"status\":\"streaming_start\"}");
    } else if (strncmp(cmd, "CMD:STOP", 8) == 0) {
        streaming = false;
        Serial.println("{\"status\":\"streaming_stop\"}");
    } else if (strncmp(cmd, "CMD:RESET", 9) == 0) {
        Serial.println("{\"status\":\"resetting\"}");
        delay(100);
        ESP.restart();
    } else if (strncmp(cmd, "CMD:RATE:", 9) == 0) {
        int ms = atoi(cmd + 9);
        if (ms >= 50 && ms <= 60000) {
            sample_interval = (uint32_t)ms;
            Serial.printf("{\"status\":\"rate_set\",\"interval_ms\":%u}\n",
                          sample_interval);
        } else {
            Serial.println("{\"error\":\"invalid_rate\"}");
        }
    } else {
        Serial.printf("{\"error\":\"unknown_cmd\",\"cmd\":\"%s\"}\n", cmd);
    }
}

// ─── Arduino Entry Points ─────────────────────────────────────────────────────

void setup() {
    Serial.begin(SERIAL_BAUD);
    while (!Serial) delay(10);

    pinMode(LED_STATUS_PIN, OUTPUT);
    analogReadResolution(12);

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(400000);  // 400 kHz I2C

    // Announce firmware version
    Serial.println("{\"status\":\"boot\",\"fw\":\"nira-v1.1\","
                   "\"proto\":\"nira-serial-v1\"}");

    fdc_configure();
    capture_baseline();

    Serial.println("{\"status\":\"ready\"}");
    last_sample_ms = millis();
}

void loop() {
    // ── Handle incoming serial commands ──────────────────────────────────────
    if (Serial.available()) {
        static char cmd_buf[64];
        static uint8_t cmd_len = 0;
        char c = Serial.read();
        if (c == '\n' || c == '\r') {
            if (cmd_len > 0) {
                cmd_buf[cmd_len] = '\0';
                handle_command(cmd_buf);
                cmd_len = 0;
            }
        } else if (cmd_len < sizeof(cmd_buf) - 1) {
            cmd_buf[cmd_len++] = c;
        }
    }

    // ── Periodic sensor sampling ──────────────────────────────────────────────
    uint32_t now = millis();
    if (streaming && (now - last_sample_ms >= sample_interval)) {
        last_sample_ms = now;

        float pF[4];
        if (!fdc_read_all(pF)) {
            Serial.println("{\"error\":\"sensor_read_failed\"}");
            digitalWrite(LED_STATUS_PIN, LOW);
            return;
        }

        float mp_index = compute_mp_index(pF);
        float temp     = read_temp_c();
        uint32_t bat   = read_bat_mv();

        // ── Emit JSON sample line ─────────────────────────────────────────────
        // Format: single line, newline-terminated — easy for Python readline()
        Serial.printf(
            "{\"ts\":%lu,\"n\":%lu,"
            "\"ch0\":%.4f,\"ch1\":%.4f,\"ch2\":%.4f,\"ch3\":%.4f,"
            "\"d0\":%.4f,\"d1\":%.4f,\"d2\":%.4f,\"d3\":%.4f,"
            "\"temp\":%.2f,\"bat_mv\":%lu,\"mp_index\":%.5f,"
            "\"mode\":\"sample\"}\n",
            (unsigned long)now,
            (unsigned long)++sample_count,
            pF[0], pF[1], pF[2], pF[3],
            pF[0] - baseline_pF[0],
            pF[1] - baseline_pF[1],
            pF[2] - baseline_pF[2],
            pF[3] - baseline_pF[3],
            isnan(temp) ? -99.0f : temp,
            (unsigned long)bat,
            mp_index
        );

        // Blink LED on each sample
        digitalWrite(LED_STATUS_PIN, HIGH);
        delay(5);
        digitalWrite(LED_STATUS_PIN, LOW);
    }
}
