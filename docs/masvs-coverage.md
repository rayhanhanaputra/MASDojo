# MASVS Coverage

The full task → MASVS → MASTG mapping for the MASDojo curriculum. Three ⭐
reference tasks are implemented end-to-end (one per dynamic grader type); task
`000` is also fully implemented as a device-free static-analysis task (solvable
and gradeable in dry-run from committed decoded resources). The rest are
scaffolded from `tasks/_template/` with complete metadata, tiered hints, and a
stubbed grader.

Authoring a new comparison-based (`flag`/`static_assert`) grader is a one-liner
via the reusable helpers in `runner/runner/graders.py` (`grade_flag` /
`grade_static`) plus a `grader/expected.json`. A CI integrity check
(`runner/tests/test_curriculum_integrity.py`) fails the build if a task is
marked `implemented` while still shipping the scaffold stub, is missing its
`expected.json`, or the prerequisite DAG has a dangling id or cycle.

> **MASTG ids:** the `MASTG-TECH-*` ids below are placeholders pending
> verification against the **current official MASTG** — ids were renumbered in
> MASTG v1.7+, so confirm each against the live guide (or fall back to the
> technique name) before publishing a task. The MASVS v2 controls are stable.

| Module | Task | id | Grader | MASVS v2 | MASTG (verify) | Status |
|:------:|------|----|:------:|----------|----------------|:------:|
| 0 | APK Anatomy & Recon | `000-apk-anatomy-recon` | static_assert | MASVS-CODE | MASTG-TECH-0007 | **implemented** |
| 0 | Lab Setup Check | `002-lab-setup-check` | static_assert | MASVS-CODE | MASTG-TECH-0001 | scaffold |
| 1 | ⭐ Find the Hardcoded API Secret | `001-find-hardcoded-secret` | static_assert | MASVS-STORAGE-1 | MASTG-TECH-0011 | **implemented** |
| 1 | Hidden Endpoint in smali | `011-hidden-endpoint-smali` | static_assert | MASVS-CODE | MASTG-TECH-0017 | scaffold |
| 1 | Patch, Rebuild & Resign | `012-patch-rebuild-resign` | flag | MASVS-CODE, MASVS-RESILIENCE-1 | MASTG-TECH-0018 | scaffold |
| 2 | Secrets in SharedPreferences/SQLite | `021-secrets-in-prefs` | flag | MASVS-STORAGE-1 | MASTG-TECH-0019 | scaffold |
| 2 | Sensitive Data in Logs | `022-sensitive-data-in-logs` | flag | MASVS-STORAGE-2 | MASTG-TECH-0021 | scaffold |
| 2 | adb Backup Extraction | `023-adb-backup-extraction` | flag | MASVS-STORAGE-1, MASVS-STORAGE-2 | MASTG-TECH-0020 | scaffold |
| 3 | Decrypt with a Recovered Key | `031-decrypt-recovered-key` | flag | MASVS-CRYPTO-1 | MASTG-TECH-0022 | scaffold |
| 3 | Break Weak Crypto | `032-break-weak-crypto` | flag | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | MASTG-TECH-0023 | scaffold |
| 4 | Hook a Method to Reveal a Runtime Flag | `041-hook-method-runtime-flag` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0028 | scaffold |
| 4 | Flip a Boolean Gate | `042-flip-boolean-gate` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0028 | scaffold |
| 5 | ⭐ Intercept & Capture the API Call | `005-intercept-api-call` | network_assert | MASVS-NETWORK-1 | MASTG-TECH-0035 | **implemented** |
| 5 | Cleartext Traffic Leak | `051-cleartext-traffic-leak` | network_assert | MASVS-NETWORK-1, MASVS-NETWORK-2 | MASTG-TECH-0035 | scaffold |
| 6 | Bypass SSL Pinning | `061-bypass-ssl-pinning` | frida_assert | MASVS-NETWORK-2, MASVS-RESILIENCE-1 | MASTG-TECH-0036 | scaffold |
| 7 | IDOR on the Backend | `071-idor-backend` | network_assert | MASVS-AUTH-1 | MASTG-TECH-0035 | scaffold |
| 7 | Broken Auth / Token Forgery | `072-broken-auth-token-forgery` | network_assert | MASVS-AUTH-1, MASVS-AUTH-2 | MASTG-TECH-0035 | scaffold |
| 8 | Exported Component / Deep Link Abuse | `081-exported-component-deeplink` | flag | MASVS-PLATFORM-1 | MASTG-TECH-0029 | scaffold |
| 8 | WebView JS-Bridge Exploit | `082-webview-jsbridge-exploit` | frida_assert | MASVS-PLATFORM-2 | MASTG-TECH-0030 | scaffold |
| 8 | Leaky Content Provider | `083-leaky-content-provider` | flag | MASVS-PLATFORM-3 | MASTG-TECH-0031 | scaffold |
| 9 | ⭐ Root Detection Bypass | `009-root-detection-bypass` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0048 | **implemented** |
| 9 | Anti-Frida / Anti-Debug Evasion | `091-anti-frida-anti-debug` | frida_assert | MASVS-RESILIENCE-2, MASVS-RESILIENCE-3 | MASTG-TECH-0048 | scaffold |
| 9 | Defeat Integrity/Tamper Check | `092-defeat-integrity-check` | flag | MASVS-RESILIENCE-4 | MASTG-TECH-0049 | scaffold |
| 10 | Full Chain Capstone | `101-full-chain` | flag | MASVS-STORAGE-1, MASVS-NETWORK-2, MASVS-AUTH-1, MASVS-RESILIENCE-1 | MASTG-TECH-0035 | scaffold |

## Coverage by MASVS category

| MASVS v2 category | Covered by |
|-------------------|-----------|
| MASVS-STORAGE | Modules 1, 2, 3 |
| MASVS-CRYPTO | Module 3 |
| MASVS-NETWORK | Modules 5, 6 |
| MASVS-AUTH | Module 7 |
| MASVS-PLATFORM | Module 8 |
| MASVS-CODE | Modules 0, 1 |
| MASVS-RESILIENCE | Modules 4, 6, 9, 10 |

## Grader-type coverage

| Grader type | Count | Reference task |
|-------------|:-----:|----------------|
| `flag` | 10 | (covered via the dynamic types) |
| `static_assert` | 4 | ⭐ `001-find-hardcoded-secret` |
| `network_assert` | 4 | ⭐ `005-intercept-api-call` |
| `frida_assert` | 6 | ⭐ `009-root-detection-bypass` |
