# Project Nira — Debugging Guide (Local Serial USB)

This guide provides step-by-step instructions to validate and debug the serial data connection between the ESP32 hardware and the host PC Python tools. 

**Note:** This only covers the local direct USB serial setup.

## 1. Verify Hardware and PlatformIO Config
Ensure your `platformio.ini` has the correct settings for USB serial debugging:
```ini
build_flags = 
    -include Arduino.h
monitor_filters = default, esp32_exception_decoder, send_on_enter
monitor_speed = 115200
```
*Note: Make sure `-include Arduino.h` is present and monitor filters provide `send_on_enter` so you can send commands easily via the serial monitor.*

## 2. Compile and Upload Firmware
1. Open up the PlatformIO IDE.
2. Build the project to verify there are no compilation errors.
3. Upload the firmware to the ESP32 via USB.

## 3. Test Raw Serial JSON Output
Before running the Python scripts, test the raw ESP32 output using the PlatformIO Serial Monitor or any other basic serial monitor (like PuTTY or the Arduino IDE Serial Monitor window).

**Steps:**
1. Open PlatformIO Serial Monitor.
2. Reset the ESP32. You should see a boot message in valid JSON format:
   `{"status":"boot","fw":"nira-v1.1","proto":"nira-serial-v1"}`
3. You should then see:
   `{"status":"zeroing"}`
   followed shortly by:
   `{"status":"zero_done","base_pF":[0.0000,0.0000,0.0000,0.0000]}` (Values will vary)
   and finally:
   `{"status":"ready"}`
4. Send `CMD:START` followed by a newline (Enter key).
5. You should see a confirmation: `{"status":"streaming_start"}` and the continuous stream of JSON sensor readings at 500ms intervals by default.
6. The streaming frames must look exactly like this:
   `{"ts":1234567,"n":1,"ch0":12.34,"ch1":12.10,"ch2":11.98,"ch3":12.05,"d0":...}`
7. Send `CMD:STOP\n` to pause the stream.

**Common Error:** Non-JSON text appearing in the stream (e.g., `ch0:12.34 ch1:...`).
*Fix:* We have already removed the non-JSON `Serial.printf` logs from `main.cpp` targeting Arduino IDE plotters. If you see non-JSON lines, double check your `main.cpp` code to ensure all `Serial.printf()` loops are wrapping output inside proper JSON string formatting like `{"key":"value"}\n`.

## 4. Test Python Hardware Alignment via `hw_test.py`
To verify that the physical hardware completely aligns with the data analysis tests:
```bash
python3 tests/hw_test.py --port /dev/ttyUSB0 --baud 115200
```
*(Replace `/dev/ttyUSB0` with your actual port, e.g., `COM3` on Windows)*

The script will run 12 sequential tests including boot parsing, zeroing, command acknowledgements, timing, and parsing of 10 consecutive data frames.

**Common Error:** `JSONDecodeError` during data frame validation.
*Fix:* This denotes leftover debug strings being printed. Use the raw serial test (Step 3) to identify the offending lines.

## 5. View Data on Python Dashboard or GUI
Once `hw_test.py` reports `✅ PASS`, your hardware works correctly and produces valid parseable JSON.

Run the gui or dashboard tools to ensure everything is graphed and compiled normally:
```bash
python3 python/nira_gui.py --port /dev/ttyUSB0
```
This should launch an interface representing the channels dynamically without exceptions.
