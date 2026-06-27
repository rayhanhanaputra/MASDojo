#!/usr/bin/env bash
# Push frida-server to the booted AVD and start it. Run once per device boot
# (the worker invokes this before grading frida_assert tasks).
set -euo pipefail

SERIAL="${1:-emulator-5554}"
FRIDA_BIN="${2:-/opt/frida-server}"

echo "[push-frida] waiting for device ${SERIAL}"
adb -s "${SERIAL}" wait-for-device
adb -s "${SERIAL}" root >/dev/null 2>&1 || true

echo "[push-frida] pushing frida-server"
adb -s "${SERIAL}" push "${FRIDA_BIN}" /data/local/tmp/frida-server
adb -s "${SERIAL}" shell "chmod 755 /data/local/tmp/frida-server"

echo "[push-frida] starting frida-server"
adb -s "${SERIAL}" shell "nohup /data/local/tmp/frida-server >/dev/null 2>&1 &"
sleep 2
echo "[push-frida] frida-server running"
