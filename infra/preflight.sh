#!/usr/bin/env bash
# MASDojo pre-flight doctor — run this BEFORE the workshop to confirm your
# machine has everything needed. It reports each check and exits non-zero if a
# REQUIRED tool is missing (recommended tools only warn).
#
#   make doctor      (or: bash infra/preflight.sh)
set -uo pipefail

green() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
red()   { printf '  \033[31m✗\033[0m %s\n' "$1"; }
warn()  { printf '  \033[33m!\033[0m %s\n' "$1"; }

MISSING=0

req() {  # req <cmd> <install-hint>
  if command -v "$1" >/dev/null 2>&1; then green "$1 ($(command -v "$1"))"
  else red "$1 missing — $2"; MISSING=$((MISSING+1)); fi
}
rec() {  # rec <cmd> <what-it's-for>
  if command -v "$1" >/dev/null 2>&1; then green "$1"
  else warn "$1 not found — $2 (recommended for solving the labs)"; fi
}

echo "== Platform (required) =="
req docker "install Docker Desktop / Docker Engine"
if docker compose version >/dev/null 2>&1; then green "docker compose"; else red "docker compose plugin missing"; MISSING=$((MISSING+1)); fi
req python3 "install Python 3.11+"
req curl "install curl"
req xz "install xz-utils (Linux) / xz (brew)"

echo "== Android / live-grading (required for Lab 2) =="
SDK="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
if [ -n "$SDK" ] && [ -d "$SDK" ]; then green "ANDROID_SDK_ROOT=$SDK"
else red "ANDROID_SDK_ROOT / ANDROID_HOME not set to an SDK dir"; MISSING=$((MISSING+1)); fi
for t in adb emulator sdkmanager avdmanager; do
  if command -v "$t" >/dev/null 2>&1; then green "$t"
  elif [ -n "$SDK" ] && { [ -x "$SDK/platform-tools/$t" ] || [ -x "$SDK/emulator/$t" ] || [ -x "$SDK/cmdline-tools/latest/bin/$t" ]; }; then green "$t (in SDK)"
  else red "$t missing — install via Android SDK cmdline-tools"; MISSING=$((MISSING+1)); fi
done

echo "== Hardware virtualization =="
case "$(uname -s)" in
  Darwin) sysctl -n kern.hv_support 2>/dev/null | grep -q 1 && green "hypervisor supported" || warn "could not confirm hypervisor (Apple Silicon: fine)";;
  Linux)  [ -e /dev/kvm ] && green "/dev/kvm present" || warn "/dev/kvm absent — enable VT-x/AMD-V in BIOS, or emulation will be slow";;
  *)      warn "on Windows use WSL2; ensure WHPX/virtualization is enabled";;
esac

echo "== Analysis tools (recommended) =="
rec frida "frida / frida-tools — dynamic instrumentation"
rec jadx "jadx — APK decompiler"
rec objection "objection — runtime mobile toolkit"
rec java "a JRE — jadx needs it"

echo
if [ "$MISSING" -eq 0 ]; then
  printf '\033[32mAll required checks passed.\033[0m Next: make solo  (then make avd-up for Lab 2)\n'
else
  printf '\033[31m%d required item(s) missing.\033[0m Install them and re-run: make doctor\n' "$MISSING"
  exit 1
fi
