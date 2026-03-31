import serial
import json
import time
import sys
import argparse

def run_hw_test(port: str, baud: int = 115200):
    PASS = []
    FAIL = []

    def ok(msg):  PASS.append(msg); print(f"  ✅ {msg}")
    def fail(msg): FAIL.append(msg); print(f"  ❌ {msg}")
    def info(msg): print(f"  🔵 {msg}")

    print(f"\n{'='*60}")
    print(f"  PROJECT NIRA — LIVE HARDWARE TEST")
    print(f"  Port: {port}  Baud: {baud}")
    print(f"{'='*60}\n")

    # ── Connect ───────────────────────────────────────────────────
    print("[ TEST 1 ] Serial Connection")
    try:
        ser = serial.Serial(port, baud, timeout=5)
        ok(f"Connected to {port}")
    except Exception as e:
        fail(f"Cannot open {port}: {e}")
        print("\n❌ HARDWARE TEST ABORTED — cannot connect")
        return

    time.sleep(2)  # wait for ESP32 boot

    # ── Flush and read boot message ────────────────────────────────
    print("\n[ TEST 2 ] Boot Status Frame")
    ser.reset_input_buffer()
    # Send a newline to wake up command parser
    ser.write(b"\n")
    boot_seen = False
    ready_seen = False
    deadline = time.time() + 10
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("status") == "boot":
                ok(f"Boot frame received — fw={obj.get('fw','?')}")
                if "proto" in obj:
                    ok(f"Protocol field present: {obj['proto']}")
                else:
                    fail("Boot frame missing 'proto' field")
                boot_seen = True
            if obj.get("status") == "ready":
                ok("Ready status received")
                ready_seen = True
                break
        except json.JSONDecodeError:
            fail(f"Non-JSON line during boot: {line}")
    if not boot_seen:
        fail("No boot status frame received in 10 seconds")
    if not ready_seen:
        fail("No 'ready' status frame received")

    # ── CMD:STOP — stop streaming ──────────────────────────────────
    print("\n[ TEST 3 ] CMD:STOP")
    ser.reset_input_buffer()
    ser.write(b"CMD:STOP\n")
    deadline = time.time() + 5
    stop_seen = False
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("status") == "streaming_stop":
                ok("CMD:STOP acknowledged — streaming_stop received")
                stop_seen = True
                break
        except json.JSONDecodeError:
            fail(f"Non-JSON response to CMD:STOP: {line}")
    if not stop_seen:
        fail("No streaming_stop response to CMD:STOP")

    # ── CMD:ZERO — baseline capture ────────────────────────────────
    print("\n[ TEST 4 ] CMD:ZERO (baseline capture)")
    ser.reset_input_buffer()
    ser.write(b"CMD:ZERO\n")
    zeroing_seen = False
    zero_done_seen = False
    baseline_valid = False
    deadline = time.time() + 15  # zeroing takes ~640ms but allow more
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("status") == "zeroing":
                ok("Zeroing status received")
                zeroing_seen = True
            if obj.get("status") == "zero_done":
                ok("Zero done status received")
                zero_done_seen = True
                bp = obj.get("base_pF", [])
                if len(bp) == 4:
                    ok(f"Baseline values: {[round(v,4) for v in bp]} pF")
                    if all(isinstance(v, (int, float)) for v in bp):
                        ok("All 4 baseline values are numeric")
                        baseline_valid = True
                    else:
                        fail("Baseline values are not all numeric")
                else:
                    fail(f"Expected 4 baseline values, got {len(bp)}")
                break
        except json.JSONDecodeError:
            fail(f"Non-JSON response to CMD:ZERO: {line}")
    if not zeroing_seen:
        fail("No 'zeroing' status from CMD:ZERO")
    if not zero_done_seen:
        fail("No 'zero_done' status from CMD:ZERO")

    # ── CMD:RATE:200 — set sample rate ────────────────────────────
    print("\n[ TEST 5 ] CMD:RATE:200")
    ser.reset_input_buffer()
    ser.write(b"CMD:RATE:200\n")
    rate_seen = False
    deadline = time.time() + 5
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("status") == "rate_set":
                if obj.get("interval_ms") == 200:
                    ok("CMD:RATE:200 acknowledged, interval_ms=200")
                else:
                    fail(f"Wrong interval_ms: {obj.get('interval_ms')}")
                rate_seen = True
                break
        except json.JSONDecodeError:
            pass
    if not rate_seen:
        fail("No rate_set response to CMD:RATE:200")

    # ── CMD:RATE:10 — invalid range ───────────────────────────────
    print("\n[ TEST 6 ] CMD:RATE:10 (invalid — should error)")
    ser.reset_input_buffer()
    ser.write(b"CMD:RATE:10\n")
    invalid_rate_seen = False
    deadline = time.time() + 5
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("error") == "invalid_rate":
                ok("Invalid rate correctly rejected")
                invalid_rate_seen = True
                break
        except json.JSONDecodeError:
            pass
    if not invalid_rate_seen:
        fail("Invalid rate not rejected (expected {\"error\":\"invalid_rate\"})")

    # ── Unknown command ───────────────────────────────────────────
    print("\n[ TEST 7 ] Unknown command")
    ser.reset_input_buffer()
    ser.write(b"CMD:BLAHBLAH\n")
    unknown_seen = False
    deadline = time.time() + 5
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("error") == "unknown_cmd":
                ok("Unknown command correctly rejected")
                unknown_seen = True
                break
        except json.JSONDecodeError:
            pass
    if not unknown_seen:
        fail("Unknown command not handled (expected {\"error\":\"unknown_cmd\"})")

    # ── CMD:START — start streaming ───────────────────────────────
    print("\n[ TEST 8 ] CMD:START — streaming data frames")
    ser.reset_input_buffer()
    ser.write(b"CMD:START\n")
    start_seen = False
    deadline = time.time() + 5
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        info(f"RX: {line}")
        try:
            obj = json.loads(line)
            if obj.get("status") == "streaming_start":
                ok("CMD:START acknowledged")
                start_seen = True
                break
        except json.JSONDecodeError:
            pass
    if not start_seen:
        fail("No streaming_start response to CMD:START")

    # ── Validate 10 consecutive data frames ───────────────────────
    print("\n[ TEST 9 ] Validate 10 data frames")
    REQUIRED_FIELDS = [
        "ts","n","ch0","ch1","ch2","ch3",
        "d0","d1","d2","d3","temp","bat_mv","mp_index","mode"
    ]
    frames_ok = 0
    frames_bad = 0
    mp_values = []
    ts_values = []
    deadline = time.time() + 20  # 10 frames × 200ms = 2s, give margin
    while frames_ok + frames_bad < 10 and time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line: continue
        try:
            obj = json.loads(line)
            if obj.get("mode") != "sample":
                info(f"Non-sample frame: {obj.get('status','?')}")
                continue
            missing = [f for f in REQUIRED_FIELDS if f not in obj]
            if missing:
                fail(f"Frame #{frames_ok+frames_bad+1} missing: {missing}")
                frames_bad += 1
            else:
                frames_ok += 1
                mp_values.append(obj["mp_index"])
                ts_values.append(obj["ts"])
                info(f"Frame {frames_ok}: mp_index={obj['mp_index']:.5f} "
                     f"bat={obj['bat_mv']}mV temp={obj['temp']:.1f}°C")
        except json.JSONDecodeError as e:
            fail(f"Invalid JSON in data frame: {e} — line: {line[:80]}")
            frames_bad += 1

    if frames_ok >= 10:
        ok(f"10/10 data frames valid")
    else:
        fail(f"Only {frames_ok}/10 data frames valid")

    # ── Timing check ──────────────────────────────────────────────
    print("\n[ TEST 10 ] Sample timing (should be ~200ms)")
    if len(ts_values) >= 2:
        intervals = [ts_values[i+1]-ts_values[i] for i in range(len(ts_values)-1)]
        avg = sum(intervals) / len(intervals)
        info(f"Average interval: {avg:.1f}ms  (expected ~200ms)")
        if 150 <= avg <= 300:
            ok(f"Sample interval within tolerance: {avg:.1f}ms")
        else:
            fail(f"Sample interval out of tolerance: {avg:.1f}ms (expected 150–300ms)")

    # ── mp_index sanity check ─────────────────────────────────────
    print("\n[ TEST 11 ] mp_index sanity")
    if mp_values:
        mn, mx, avg = min(mp_values), max(mp_values), sum(mp_values)/len(mp_values)
        info(f"mp_index — min: {mn:.5f}  max: {mx:.5f}  avg: {avg:.5f}")
        if all(v >= 0 for v in mp_values):
            ok("All mp_index values are non-negative")
        else:
            fail("Negative mp_index detected (impossible by formula)")
        if mx < 100:
            ok("mp_index within physical range (<100 pF RMS)")
        else:
            fail(f"mp_index suspiciously large: {mx}")

    # ── CMD:STOP final ────────────────────────────────────────────
    print("\n[ TEST 12 ] CMD:STOP final")
    ser.write(b"CMD:STOP\n")
    time.sleep(0.5)
    ser.close()
    ok("Serial port closed cleanly")

    # ── Summary ───────────────────────────────────────────────────
    total = len(PASS) + len(FAIL)
    print(f"\n{'='*60}")
    print(f"  HARDWARE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  ✅ PASSED: {len(PASS)}/{total}")
    print(f"  ❌ FAILED: {len(FAIL)}/{total}")
    if FAIL:
        print(f"\n  Failed items:")
        for f in FAIL:
            print(f"    ❌ {f}")
    print(f"\n  VERDICT: {'✅ PASS' if not FAIL else '❌ FAIL'}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Serial port e.g. /dev/ttyUSB0 or COM4")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()
    run_hw_test(args.port, args.baud)
