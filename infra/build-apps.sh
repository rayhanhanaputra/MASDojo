#!/usr/bin/env bash
# Build the intentionally-vulnerable training apps and copy each resulting APK
# into the matching task package as app/target.apk.
#
#   infra/build-apps.sh            # build all apps
#   infra/build-apps.sh pulse      # build a single app
#
# Requires a JDK 17 and the Android SDK (ANDROID_SDK_ROOT / ANDROID_HOME set).
# Uses ./gradlew if a wrapper is present, otherwise a system `gradle`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="${REPO_ROOT}/apps"

# app name -> destination task package (relative to repo root)
declare -A TASK_FOR=(
  [securenotes]="tasks/001-find-hardcoded-secret"
  [pulse]="tasks/005-intercept-api-call"
  [vaultguard]="tasks/009-root-detection-bypass"
)

build_one() {
  local app="$1"
  local dest="${TASK_FOR[$app]:-}"
  if [[ -z "${dest}" ]]; then
    echo "!! unknown app '${app}' (no task mapping)" >&2
    return 1
  fi

  echo "==> building ${app}"
  pushd "${APPS_DIR}/${app}" >/dev/null

  # Generate a committed-quality wrapper if one isn't present, so subsequent
  # builds are pinned to a known Gradle version rather than the host's.
  if [[ ! -x ./gradlew ]]; then
    echo "    (no gradlew — generating wrapper)"
    gradle --no-daemon wrapper --gradle-version "${GRADLE_VERSION:-8.7}"
  fi
  ./gradlew --no-daemon :app:assembleDebug

  local apk
  apk="$(find app/build/outputs/apk/debug -name '*.apk' | head -n1)"
  if [[ -z "${apk}" ]]; then
    echo "!! no APK produced for ${app}" >&2
    popd >/dev/null
    return 1
  fi

  mkdir -p "${REPO_ROOT}/${dest}/app"
  cp "${apk}" "${REPO_ROOT}/${dest}/app/target.apk"
  echo "    -> ${dest}/app/target.apk"
  popd >/dev/null
}

if [[ $# -gt 0 ]]; then
  for app in "$@"; do build_one "${app}"; done
else
  for app in "${!TASK_FOR[@]}"; do build_one "${app}"; done
fi

echo "==> done"
