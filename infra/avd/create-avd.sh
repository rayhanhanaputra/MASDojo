#!/usr/bin/env bash
# Create the AVD the runner boots. Invoked from runner/Dockerfile.
set -euo pipefail

SYSTEM_IMAGE="${1:-system-images;android-34;google_apis;x86_64}"
AVD_NAME="${2:-masdojo_avd}"
SDK_ROOT="${ANDROID_SDK_ROOT:-/opt/android-sdk}"
AVDMANAGER="${SDK_ROOT}/cmdline-tools/latest/bin/avdmanager"

echo "[create-avd] creating AVD '${AVD_NAME}' from ${SYSTEM_IMAGE}"
echo "no" | "${AVDMANAGER}" create avd \
  --force \
  --name "${AVD_NAME}" \
  --package "${SYSTEM_IMAGE}" \
  --device "pixel_5"

# A little extra RAM/heap keeps app launches snappy under grading load.
AVD_CONFIG="${ANDROID_AVD_HOME:-/root/.android/avd}/${AVD_NAME}.avd/config.ini"
if [[ -f "${AVD_CONFIG}" ]]; then
  {
    echo "hw.ramSize=2048"
    echo "vm.heapSize=512"
    echo "hw.keyboard=yes"
  } >> "${AVD_CONFIG}"
fi

echo "[create-avd] done"
