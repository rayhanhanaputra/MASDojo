#!/usr/bin/env bash
# Provision a local AVD for MASDojo's live Frida/RASP grading (Lab 2).
#
# One command: create a rootable AVD, boot it, `adb root`, then download and
# launch a frida-server that matches the host architecture. The participant runs
# this once on their own laptop; the runner (in attach mode, RUNNER_ATTACH=true)
# then grades against it — no cloud, no KVM VM.
#
#   infra/avd-up.sh              # create + boot + root + frida
#   AVD_NAME=foo infra/avd-up.sh # override the AVD name
#
# Requires: the Android SDK (sdkmanager, avdmanager, emulator, adb) with
# ANDROID_SDK_ROOT (or ANDROID_HOME) set; curl; xz. Hardware virtualization must
# be enabled (Apple Silicon / Intel VT-x / AMD-V).
set -euo pipefail

AVD_NAME="${AVD_NAME:-masdojo_avd}"
API="${ANDROID_API_LEVEL:-34}"
FRIDA_VERSION="${FRIDA_VERSION:-16.4.8}"
SERIAL="${EMULATOR_SERIAL:-emulator-5554}"

SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
[ -n "$SDK" ] || { echo "!! set ANDROID_SDK_ROOT (or ANDROID_HOME) to your Android SDK path"; exit 1; }

# Resolve a tool from the SDK layout, falling back to PATH.
resolve() {
  local name="$1"; shift
  local p
  for p in "$@"; do [ -x "$p" ] && { echo "$p"; return; }; done
  command -v "$name" >/dev/null 2>&1 && { echo "$name"; return; }
  echo "!! could not find '$name' (looked under \$ANDROID_SDK_ROOT and PATH)" >&2
  exit 1
}

SDKMANAGER="$(resolve sdkmanager "$SDK/cmdline-tools/latest/bin/sdkmanager" "$SDK/cmdline-tools/bin/sdkmanager")"
AVDMANAGER="$(resolve avdmanager "$SDK/cmdline-tools/latest/bin/avdmanager" "$SDK/cmdline-tools/bin/avdmanager")"
EMULATOR="$(resolve emulator "$SDK/emulator/emulator")"
ADB="$(resolve adb "$SDK/platform-tools/adb")"
command -v curl >/dev/null 2>&1 || { echo "!! missing 'curl'"; exit 1; }
command -v xz >/dev/null 2>&1 || { echo "!! missing 'xz'"; exit 1; }

# Map the host architecture to the emulator ABI + frida-server arch.
case "$(uname -m)" in
  arm64|aarch64) ABI="arm64-v8a"; FRIDA_ARCH="arm64" ;;
  x86_64|amd64)  ABI="x86_64";    FRIDA_ARCH="x86_64" ;;
  *) echo "!! unsupported host arch: $(uname -m)"; exit 1 ;;
esac
# google_apis (not google_play) permits `adb root`.
IMAGE="system-images;android-${API};google_apis;${ABI}"

echo "==> installing system image: $IMAGE"
yes | "$SDKMANAGER" --licenses >/dev/null 2>&1 || true
"$SDKMANAGER" "$IMAGE" "platform-tools" "emulator" >/dev/null

echo "==> creating AVD '$AVD_NAME' (--force overwrites any existing one)"
echo "no" | "$AVDMANAGER" create avd -n "$AVD_NAME" -k "$IMAGE" --force >/dev/null

echo "==> booting AVD headless (writable-system for root)"
"$EMULATOR" -avd "$AVD_NAME" -no-window -no-audio -no-boot-anim \
  -writable-system -no-snapshot -gpu swiftshader_indirect >/dev/null 2>&1 &

echo "==> waiting for boot…"
"$ADB" -s "$SERIAL" wait-for-device
until [ "$("$ADB" -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do
  sleep 2
done

echo "==> enabling root (adb root)"
"$ADB" -s "$SERIAL" root >/dev/null 2>&1 || true
sleep 3
"$ADB" -s "$SERIAL" wait-for-device

echo "==> downloading frida-server $FRIDA_VERSION ($FRIDA_ARCH)"
FS="frida-server-${FRIDA_VERSION}-android-${FRIDA_ARCH}"
URL="https://github.com/frida/frida/releases/download/${FRIDA_VERSION}/${FS}.xz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$URL" -o "$TMP/fs.xz"
xz -d "$TMP/fs.xz"   # -> $TMP/fs

echo "==> pushing + launching frida-server"
"$ADB" -s "$SERIAL" push "$TMP/fs" /data/local/tmp/frida-server >/dev/null
"$ADB" -s "$SERIAL" shell chmod 755 /data/local/tmp/frida-server
# Launch detached; ignore the shell returning immediately.
"$ADB" -s "$SERIAL" shell "nohup /data/local/tmp/frida-server >/dev/null 2>&1 &" || true
sleep 2

if "$ADB" -s "$SERIAL" shell pidof frida-server >/dev/null 2>&1; then
  echo "==> done. AVD '$AVD_NAME' is up, rooted, frida-server running."
  echo "    Now start the runner in attach mode:  make runner-host"
else
  echo "!! frida-server did not come up. Check 'adb -s $SERIAL logcat' and re-run." >&2
  exit 1
fi
