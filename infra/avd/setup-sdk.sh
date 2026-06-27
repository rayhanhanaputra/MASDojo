#!/usr/bin/env bash
# Install the Android command-line tools, platform-tools, emulator, a system
# image, and a matching frida-server. Invoked from runner/Dockerfile.
set -euo pipefail

ANDROID_API="${1:-34}"
SYSTEM_IMAGE="${2:-system-images;android-34;google_apis;x86_64}"
SDK_ROOT="${ANDROID_SDK_ROOT:-/opt/android-sdk}"
FRIDA_VERSION="${FRIDA_VERSION:-16.4.8}"
CMDLINE_TOOLS_VERSION="11076708"  # commandlinetools-linux build

mkdir -p "${SDK_ROOT}/cmdline-tools"
cd /tmp

echo "[setup-sdk] downloading command-line tools"
curl -fsSL -o cmdline-tools.zip \
  "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip"
unzip -q cmdline-tools.zip -d "${SDK_ROOT}/cmdline-tools"
mv "${SDK_ROOT}/cmdline-tools/cmdline-tools" "${SDK_ROOT}/cmdline-tools/latest"
rm -f cmdline-tools.zip

SDKMANAGER="${SDK_ROOT}/cmdline-tools/latest/bin/sdkmanager"
yes | "${SDKMANAGER}" --licenses >/dev/null 2>&1 || true

echo "[setup-sdk] installing platform-tools, emulator, platform, and system image"
"${SDKMANAGER}" \
  "platform-tools" \
  "emulator" \
  "platforms;android-${ANDROID_API}" \
  "${SYSTEM_IMAGE}"

echo "[setup-sdk] fetching frida-server ${FRIDA_VERSION} (x86_64)"
curl -fsSL -o /opt/frida-server.xz \
  "https://github.com/frida/frida/releases/download/${FRIDA_VERSION}/frida-server-${FRIDA_VERSION}-android-x86_64.xz"
xz -d /opt/frida-server.xz
chmod +x /opt/frida-server

echo "[setup-sdk] done"
