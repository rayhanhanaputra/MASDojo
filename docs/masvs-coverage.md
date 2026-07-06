# MASVS Coverage

The full task → MASVS → MASTG mapping for the MASDojo curriculum. **Every one of
the 24 tasks is implemented with a real payload-detection grader** — the system
that verifies the learner genuinely applied the technique, not just that they
found the right shape. Three ⭐ reference tasks (`001`/`005`/`009`) additionally
drive a live Android emulator; the rest are solvable and gradeable **now, in
dry-run** from committed artifacts (decoded resources, prefs/log/backup dumps,
encrypted blobs, captured traffic) — no emulator or APK build required.

How each technique is detected:

- **Static / storage / platform / network analysis** — the learner submits the
  value they recovered; the grader confirms it matches AND genuinely appears in
  the committed artifact (so the format alone can't be guessed).
- **Cryptography** — the learner submits the plaintext they decrypted; it can't
  be guessed, so a correct value *is* proof they performed the decryption. The
  committed ciphertext is real (CI decrypts it to the flag).
- **Frida** — the learner submits a script; on a KVM host it is injected and its
  runtime effect asserted, and in dry-run it is statically validated (does it
  hook the right class + method and enforce the required behaviour?).

Authoring a new comparison grader is a one-liner via the reusable helpers in
`runner/runner/graders.py` (`grade_recovered` / `grade_flag` /
`grade_frida_script`) plus a `grader/expected.json`. CI integrity checks
(`runner/tests/test_curriculum_integrity.py`, `test_all_tasks_gradeable.py`)
fail the build if a task is marked `implemented` while shipping the scaffold
stub, is missing its `expected.json`, doesn't PASS its own correct answer while
rejecting a wrong one, or the prerequisite DAG has a dangling id or cycle.

> **MASTG ids:** the `MASTG-TECH-*` ids below are placeholders pending
> verification against the **current official MASTG** — ids were renumbered in
> MASTG v1.7+, so confirm each against the live guide (or fall back to the
> technique name) before publishing a task. The MASVS v2 controls are stable.

| Module | Task | id | Grader | MASVS v2 | MASTG (verify) | Status |
|:------:|------|----|:------:|----------|----------------|:------:|
| 0 | APK Anatomy & Recon | `000-apk-anatomy-recon` | static_assert | MASVS-CODE | MASTG-TECH-0007 | **implemented** |
| 0 | Lab Setup Check | `002-lab-setup-check` | static_assert | MASVS-CODE | MASTG-TECH-0001 | **implemented** |
| 1 | ⭐ Find the Hardcoded API Secret | `001-find-hardcoded-secret` | static_assert | MASVS-STORAGE-1 | MASTG-TECH-0011 | **implemented** |
| 1 | Hidden Endpoint in smali | `011-hidden-endpoint-smali` | static_assert | MASVS-CODE | MASTG-TECH-0017 | **implemented** |
| 1 | Patch, Rebuild & Resign | `012-patch-rebuild-resign` | flag | MASVS-CODE, MASVS-RESILIENCE-1 | MASTG-TECH-0018 | **implemented** |
| 2 | Secrets in SharedPreferences/SQLite | `021-secrets-in-prefs` | flag | MASVS-STORAGE-1 | MASTG-TECH-0019 | **implemented** |
| 2 | Sensitive Data in Logs | `022-sensitive-data-in-logs` | flag | MASVS-STORAGE-2 | MASTG-TECH-0021 | **implemented** |
| 2 | adb Backup Extraction | `023-adb-backup-extraction` | flag | MASVS-STORAGE-1, MASVS-STORAGE-2 | MASTG-TECH-0020 | **implemented** |
| 3 | Decrypt with a Recovered Key | `031-decrypt-recovered-key` | flag | MASVS-CRYPTO-1 | MASTG-TECH-0022 | **implemented** |
| 3 | Break Weak Crypto | `032-break-weak-crypto` | flag | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | MASTG-TECH-0023 | **implemented** |
| 4 | Hook a Method to Reveal a Runtime Flag | `041-hook-method-runtime-flag` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0028 | **implemented** |
| 4 | Flip a Boolean Gate | `042-flip-boolean-gate` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0028 | **implemented** |
| 5 | ⭐ Intercept & Capture the API Call | `005-intercept-api-call` | network_assert | MASVS-NETWORK-1 | MASTG-TECH-0035 | **implemented** |
| 5 | Cleartext Traffic Leak | `051-cleartext-traffic-leak` | network_assert | MASVS-NETWORK-1, MASVS-NETWORK-2 | MASTG-TECH-0035 | **implemented** |
| 6 | Bypass SSL Pinning | `061-bypass-ssl-pinning` | frida_assert | MASVS-NETWORK-2, MASVS-RESILIENCE-1 | MASTG-TECH-0036 | **implemented** |
| 7 | IDOR on the Backend | `071-idor-backend` | network_assert | MASVS-AUTH-1 | MASTG-TECH-0035 | **implemented** |
| 7 | Broken Auth / Token Forgery | `072-broken-auth-token-forgery` | network_assert | MASVS-AUTH-1, MASVS-AUTH-2 | MASTG-TECH-0035 | **implemented** |
| 8 | Exported Component / Deep Link Abuse | `081-exported-component-deeplink` | flag | MASVS-PLATFORM-1 | MASTG-TECH-0029 | **implemented** |
| 8 | WebView JS-Bridge Exploit | `082-webview-jsbridge-exploit` | static_assert | MASVS-PLATFORM-2 | MASTG-TECH-0030 | **implemented** |
| 8 | Leaky Content Provider | `083-leaky-content-provider` | flag | MASVS-PLATFORM-3 | MASTG-TECH-0031 | **implemented** |
| 9 | ⭐ Root Detection Bypass | `009-root-detection-bypass` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0048 | **implemented** |
| 9 | Anti-Frida / Anti-Debug Evasion | `091-anti-frida-anti-debug` | frida_assert | MASVS-RESILIENCE-2, MASVS-RESILIENCE-3 | MASTG-TECH-0048 | **implemented** |
| 9 | Defeat Integrity/Tamper Check | `092-defeat-integrity-check` | flag | MASVS-RESILIENCE-4 | MASTG-TECH-0049 | **implemented** |
| 10 | Full Chain Capstone | `101-full-chain` | flag | MASVS-STORAGE-1, MASVS-NETWORK-2, MASVS-AUTH-1, MASVS-RESILIENCE-1 | MASTG-TECH-0035 | **implemented** |

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

| Grader type | Count | Implemented | Reference (live-device) task |
|-------------|:-----:|:-----------:|----------------|
| `flag` | 10 | 10 | recovered-value detection |
| `static_assert` | 5 | 5 | ⭐ `001-find-hardcoded-secret` |
| `network_assert` | 4 | 4 | ⭐ `005-intercept-api-call` |
| `frida_assert` | 5 | 5 | ⭐ `009-root-detection-bypass` |

All 24 tasks pass their own PASS/FAIL detection test in dry-run
(`runner/tests/test_all_tasks_gradeable.py`).
