#!/usr/bin/env bash
# Install the mitmproxy CA into the AVD's SYSTEM trust store so HTTPS traffic is
# interceptable (unblocks HTTPS network_assert and the SSL-pinning task). Run
# once at snapshot-build time against an emulator booted with -writable-system.
set -euo pipefail

SERIAL="${1:-emulator-5554}"
CA="${2:-${HOME}/.mitmproxy/mitmproxy-ca-cert.cer}"

if [[ ! -f "${CA}" ]]; then
  echo "[mitm-ca] CA not found at ${CA}; run mitmproxy once to generate it" >&2
  exit 1
fi

# Android names system CAs by the old OpenSSL subject hash + .0
HASH="$(openssl x509 -inform PEM -subject_hash_old -in "${CA}" | head -n1)"
echo "[mitm-ca] installing CA as ${HASH}.0"

# After `adb root` adbd restarts as root (shell is already root; `su` is absent
# on google_apis images). Wait for it to come back before remounting /system.
adb -s "${SERIAL}" root
adb -s "${SERIAL}" wait-for-device
adb -s "${SERIAL}" remount || true
DEST="/system/etc/security/cacerts/${HASH}.0"
adb -s "${SERIAL}" push "${CA}" "${DEST}"
adb -s "${SERIAL}" shell "chmod 644 ${DEST}"
adb -s "${SERIAL}" shell "[ -f ${DEST} ]"
echo "[mitm-ca] done — HTTPS is now interceptable on this device"
