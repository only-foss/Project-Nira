# Nira Serial Protocol Reference
_Auto-generated — do not edit manually. Edit main.cpp and regenerate._
_Firmware: nira-v1.1 | Protocol: nira-serial-v1_

## Transport

| Parameter | Value |
|-----------|-------|
| Interface | USB CDC (Serial over USB) |
| Baud rate | 115200 |
| Line ending | `\n` (LF) |
| Encoding | UTF-8 |
| Direction | Bidirectional |

## Data Frame (Device → Host)

One JSON object per line, newline-terminated. Fields:

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `ts` | uint32 | ms | Device uptime in milliseconds |
| `n` | uint32 | — | Sample sequence number (monotonic) |
| `ch0`–`ch3` | float | pF | Raw capacitance per channel |
| `d0`–`d3` | float | pF | Delta from baseline per channel |
| `temp` | float | °C | Die temperature; −99 if unavailable |
| `bat_mv` | uint32 | mV | Battery voltage |
| `mp_index` | float | pF RMS | Microplastic index = √(mean(dᵢ²)) |
| `mode` | string | — | Always `"sample"` for data frames |

### Example
```json
{"ts":12345,"n":42,"ch0":12.3401,"ch1":12.1003,"ch2":11.9812,"ch3":12.0540,
 "d0":0.0021,"d1":-0.0132,"d2":0.0088,"d3":-0.0044,
 "temp":28.5,"bat_mv":3820,"mp_index":0.00821,"mode":"sample"}
```

## Status Frames (Device → Host)

| `status` | Extra fields | Meaning |
|----------|-------------|---------|
| `"boot"` | `fw`, `proto` | Device powered on |
| `"zeroing"` | — | Baseline capture started |
| `"zero_done"` | `base_pF[4]` | Baseline captured |
| `"ready"` | — | Ready to stream |
| `"streaming_start"` | — | Streaming resumed |
| `"streaming_stop"` | — | Streaming paused |
| `"resetting"` | — | Device restarting |
| `"rate_set"` | `interval_ms` | Sample rate updated |

## Error Frames

```json
{"error": "sensor_read_failed"}
{"error": "unknown_cmd", "cmd": "..."}
{"error": "invalid_rate"}
```

## Control Commands (Host → Device)

ASCII, newline-terminated (`\n`):

| Command | Range | Effect |
|---------|-------|--------|
| `CMD:START` | — | Resume streaming |
| `CMD:STOP` | — | Pause streaming |
| `CMD:ZERO` | — | Re-capture baseline (32 samples) |
| `CMD:RATE:<ms>` | 50–60000 | Set sample interval |
| `CMD:RESET` | — | Software restart |

## Microplastic Index Formula

```
mp_index = sqrt( (d0² + d1² + d2² + d3²) / 4 )
```

Where `dᵢ = chᵢ − baseline_chᵢ`. Alert threshold: **0.10 pF RMS**.
