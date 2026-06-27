# 005 — Intercept & Capture the API Call  ⭐ reference task

**Grader type:** `network_assert` · **MASVS:** MASVS-NETWORK-1

## The vulnerability
`apps/pulse` sends a device token to its telemetry endpoint on startup over
plain HTTP with no certificate pinning. Anyone on-path (or running an
intercepting proxy on a controlled device) can read the token.

## How the grader proves it
1. The runner starts the bundled mock backend (`backend/server.py`, stdlib-only)
   and an mitmproxy recorder, sets the emulator's HTTP proxy to mitmproxy, and
   launches the app.
2. Pulse POSTs `device_token=FLAG{...}` to `/api/v1/telemetry`; mitmproxy records
   the flow.
3. `grader/grade.py` asserts the telemetry request was captured, that it carried
   the expected token, and that the learner submitted the same value they
   intercepted.

## Rebuilding the target
```bash
infra/build-apps.sh pulse
# produces tasks/005-intercept-api-call/app/target.apk
```
The endpoint host/port (`10.0.2.2:8090`) and the token are defined in
`apps/pulse`; keep them in sync with `grader/expected.json` and `backend/server.py`.
