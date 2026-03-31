# Project Nira — Firmware API Reference
_Auto-generated from main.cpp Doxygen comments_
_Firmware: nira-v1.1_

## File: `firmware/v1.0_esp32_fdc1004/src/main.cpp`

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `FDC1004_ADDR` | 0x50 | I2C address (ADDR pin → GND) |
| `I2C_SDA_PIN` | 21 | SDA GPIO |
| `I2C_SCL_PIN` | 22 | SCL GPIO |
| `LED_STATUS_PIN` | 2 | Onboard LED GPIO |
| `BAT_ADC_PIN` | 34 | Battery ADC GPIO |
| `SERIAL_BAUD` | 115200 | UART baud rate |
| `DEFAULT_SAMPLE_MS` | 500 | Default sample interval (ms) |
| `BASELINE_SAMPLES` | 32 | Samples averaged for baseline |
| `DANGER_THRESH` (GUI) | 0.10 | MP alert threshold (pF RMS) |

### Functions

#### `fdc_write16(reg, val) → bool`
Write a 16-bit value to an FDC1004 I2C register.  
Returns `true` on success.

#### `fdc_read_meas(msb_reg) → int32_t`
Read a 24-bit two's complement measurement from the FDC1004.  
`msb_reg`: one of `MEAS1_MSB`..`MEAS4_MSB`.

#### `raw_to_pF(raw) → float`
Convert 24-bit signed integer to picofarads.  
Formula: `raw × 30.0 / 2^24`. Full scale = ±15 pF.

#### `fdc_configure()`
Configure all 4 FDC1004 channels: CHA=CHx, CHB=CAPDAC, CAPDAC=0, rate=100 S/s.  
Call once in `setup()`.

#### `fdc_read_all(pF[4]) → bool`
Trigger a single-shot measurement and read all 4 channels into `pF[]`.  
Returns `false` on I2C error.

#### `read_bat_mv() → uint32_t`
Read battery voltage via ADC on `BAT_ADC_PIN`.  
Assumes 1:2 voltage divider, 3.3 V reference, 12-bit ADC.

#### `read_temp_c() → float`
Read ESP32 internal die temperature. Returns `NAN` if unavailable.

#### `compute_mp_index(pF[4]) → float`
Compute RMS deviation from baseline across 4 channels.  
Formula: `sqrt(mean((pF[i] - baseline_pF[i])^2))`.  
Output JSON field: `mp_index`.

#### `capture_baseline()`
Average `BASELINE_SAMPLES` readings into `baseline_pF[]`.  
Emits `{"status":"zeroing"}` then `{"status":"zero_done","base_pF":[...]}`.  
Called on boot and on `CMD:ZERO`.

#### `handle_command(cmd)`
Parse and execute a `CMD:*` ASCII command string.  
Supported: `CMD:START`, `CMD:STOP`, `CMD:ZERO`, `CMD:RATE:<ms>`, `CMD:RESET`.

#### `setup()`
Arduino entry point: init Serial, I2C, FDC1004, baseline. Emits `{"status":"ready"}`.

#### `loop()`
Arduino main loop: drain serial command buffer → periodic sample → emit JSON.
