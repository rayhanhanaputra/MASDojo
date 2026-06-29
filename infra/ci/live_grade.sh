#!/usr/bin/env bash
# Live field-verification: submit the three reference tasks to a running MASDojo
# and assert the real emulator grades each correct answer PASS and a wrong answer
# FAIL. Intended to run on a KVM host with the full stack up (see
# .github/workflows/kvm-live-grade.yml). Exits non-zero on any mismatch.
set -euo pipefail

API="${API:-http://localhost:8000}"
EMAIL="ci+$(date +%s)@masdojo.test"
PASS="password123"

jq_get() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo "==> register + login"
curl -fsS -X POST "$API/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"display_name\":\"CI\",\"password\":\"$PASS\"}" >/dev/null
TOK="$(curl -fsS -X POST "$API/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" | jq_get "['access_token']")"

FRIDA_BYPASS='Java.perform(function(){Java.use("org.masdojo.vaultguard.RootChecker").isDeviceRooted.implementation=function(){return false;};});'

# task_id | payload json | expected status
submit_and_wait() {
  local task="$1" payload="$2" want="$3"
  local sid status
  sid="$(curl -fsS -X POST "$API/submissions/$task" -H "Authorization: Bearer $TOK" \
    -H 'Content-Type: application/json' -d "{\"payload\":$payload}" | jq_get "['id']")"
  for _ in $(seq 1 80); do
    # Tolerate a transient blip in the poll; only a terminal status is authoritative.
    status="$(curl -fsS "$API/submissions/$sid" -H "Authorization: Bearer $TOK" 2>/dev/null \
      | jq_get "['status']" 2>/dev/null)" || { sleep 3; continue; }
    case "$status" in passed|failed|error) break;; esac
    sleep 3
  done
  if [[ "$status" != "$want" ]]; then
    echo "!! $task: expected $want, got $status (submission $sid)" >&2
    curl -fsS "$API/submissions/$sid" -H "Authorization: Bearer $TOK" >&2
    return 1
  fi
  echo "   ok: $task -> $status"
}

echo "==> 001 static_assert (PASS then FAIL)"
submit_and_wait "001-find-hardcoded-secret" '{"value":"msd_live_sk_8f3c1d77a94b42e0b6c5e9f0a1d2c3b4"}' passed
submit_and_wait "001-find-hardcoded-secret" '{"value":"msd_live_sk_wrong"}' failed

echo "==> 005 network_assert (PASS then FAIL)"
submit_and_wait "005-intercept-api-call" '{"value":"FLAG{n3tw0rk_1nt3rc3pt3d}"}' passed
submit_and_wait "005-intercept-api-call" '{"value":"FLAG{wrong}"}' failed

echo "==> 009 frida_assert (PASS then FAIL)"
submit_and_wait "009-root-detection-bypass" "{\"script\":$(python3 -c "import json,sys;print(json.dumps('$FRIDA_BYPASS'))")}" passed
submit_and_wait "009-root-detection-bypass" '{"script":"Java.perform(function(){});"}' failed

echo "==> all live PASS/FAIL assertions held"
