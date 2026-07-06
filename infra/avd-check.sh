#!/usr/bin/env bash
# Pre-flight healthcheck for MASDojo's live-grading path. Run this before the
# workshop to confirm the local AVD is ready for Lab 2 (Frida/RASP).
#
#   infra/avd-check.sh
#
# Exits non-zero (with a clear message) on the first failed check.
set -uo pipefail

SERIAL="${EMULATOR_SERIAL:-emulator-5554}"
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
ADB="adb"
[ -n "$SDK" ] && [ -x "$SDK/platform-tools/adb" ] && ADB="$SDK/platform-tools/adb"

fail() { echo "  ✗ $1"; echo; echo "Not ready. Run 'make avd-up' first."; exit 1; }
ok()   { echo "  ✓ $1"; }

echo "MASDojo pre-flight (target: $SERIAL)"

command -v "$ADB" >/dev/null 2>&1 || fail "adb not found (set ANDROID_SDK_ROOT / install platform-tools)"
ok "adb present"

"$ADB" -s "$SERIAL" get-state 2>/dev/null | grep -q device || fail "AVD $SERIAL is not running"
ok "AVD $SERIAL is online"

[ "$("$ADB" -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ] \
  || fail "AVD has not finished booting"
ok "AVD boot completed"

# adb root available (google_apis image) — needed to run frida-server.
"$ADB" -s "$SERIAL" shell 'id' 2>/dev/null | grep -q 'uid=0' \
  || echo "  ! shell is not root yet (run: adb -s $SERIAL root)"

"$ADB" -s "$SERIAL" shell pidof frida-server >/dev/null 2>&1 \
  || fail "frida-server is not running on the device"
ok "frida-server running"

echo
echo "Ready. Start grading:  make runner-host   (RUNNER_ATTACH=true)"
