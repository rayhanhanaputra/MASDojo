# MASVS Coverage

The full task → MASVS → MASTG mapping for the MASDojo curriculum. **Every one of
the 30 tasks is implemented with a real payload-detection grader** — the system
that verifies the learner genuinely applied the technique, not just that they
found the right shape. Three ⭐ reference tasks (`001`/`005`/`009`) additionally
drive a live Android emulator; most others are solvable and gradeable **now, in
dry-run** from committed artifacts (obfuscated code/resources, encoded prefs/log
dumps, packed backups, real ciphertext, captured traffic), while the API-abuse
and capstone tasks exploit the bundled live `vulnapi`.

**No copy-paste.** The challenge files never contain the answer verbatim — the
learner must *apply the technique* to derive it: base64/XOR-deobfuscate a value
in decompiled code, reconstruct an obfuscated string in smali, unpack a
gzip'd/tar backup, decrypt a real ciphertext, triage which third-party request
leaks PII, or exploit the live `vulnapi` (IDOR / alg:none forge). Seeded tasks
are also per-learner, so a derived answer can't be shared either.

How each technique is detected:

- **Static / storage / platform / network analysis** — the learner submits the
  value they *derived* (decoded, deobfuscated, unpacked, or triaged from the
  challenge files); the grader constant-time compares it to the seed-specific
  answer. The answer is never in the files verbatim, so guessing the format
  doesn't help.
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

> **MASTG ids:** the reverse-engineering, dynamic-instrumentation, network-
> interception, and root/pinning-bypass techniques below were verified against
> the **current** MASTG (mas.owasp.org) — e.g. `MASTG-TECH-0023` Reviewing
> Decompiled Java Code, `MASTG-TECH-0043` Method Hooking, `MASTG-TECH-0011`
> Setting Up an Interception Proxy, `MASTG-TECH-0012` Bypassing Certificate
> Pinning, `MASTG-TECH-0144` Bypassing Root Detection, `MASTG-TECH-0004`
> Repackaging Apps. The storage / crypto / platform rows reference the closest
> current technique or test; for those the **MASVS v2 control + technique name
> are authoritative** (the MASTG catalog reorganizes ids periodically).

| Module | Task | id | Grader | MASVS v2 | MASTG | Status |
|:------:|------|----|:------:|----------|----------------|:------:|
| 0 | APK Anatomy & Recon | `000-apk-anatomy-recon` | static_assert | MASVS-CODE | MASTG-TECH-0007 | **implemented** |
| 0 | Lab Setup Check | `002-lab-setup-check` | static_assert | MASVS-CODE | MASTG-TECH-0001 | **implemented** |
| 1 | ⭐ Find the Hardcoded API Secret | `001-find-hardcoded-secret` | static_assert | MASVS-STORAGE-1 | MASTG-TECH-0023 | **implemented** |
| 1 | Hidden Endpoint in smali | `011-hidden-endpoint-smali` | static_assert | MASVS-CODE | MASTG-TECH-0017 | **implemented** |
| 1 | Patch, Rebuild & Resign | `012-patch-rebuild-resign` | flag | MASVS-CODE, MASVS-RESILIENCE-1 | MASTG-TECH-0004 | **implemented** |
| 2 | Secrets in SharedPreferences/SQLite | `021-secrets-in-prefs` | flag | MASVS-STORAGE-1 | MASTG-TECH-0019 | **implemented** |
| 2 | Sensitive Data in Logs | `022-sensitive-data-in-logs` | flag | MASVS-STORAGE-2 | MASTG-TECH-0021 | **implemented** |
| 2 | adb Backup Extraction | `023-adb-backup-extraction` | flag | MASVS-STORAGE-1, MASVS-STORAGE-2 | MASTG-TECH-0020 | **implemented** |
| 3 | Decrypt with a Recovered Key | `031-decrypt-recovered-key` | flag | MASVS-CRYPTO-1 | MASTG-TECH-0022 | **implemented** |
| 3 | Break Weak Crypto | `032-break-weak-crypto` | flag | MASVS-CRYPTO-1, MASVS-CRYPTO-2 | MASTG-TECH-0023 | **implemented** |
| 4 | Hook a Method to Reveal a Runtime Flag | `041-hook-method-runtime-flag` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0043 | **implemented** |
| 4 | Flip a Boolean Gate | `042-flip-boolean-gate` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0043 | **implemented** |
| 5 | ⭐ Intercept & Capture the API Call | `005-intercept-api-call` | network_assert | MASVS-NETWORK-1 | MASTG-TECH-0011 | **implemented** |
| 5 | Cleartext Traffic Leak | `051-cleartext-traffic-leak` | network_assert | MASVS-NETWORK-1, MASVS-NETWORK-2 | MASTG-TECH-0011 | **implemented** |
| 6 | Bypass SSL Pinning | `061-bypass-ssl-pinning` | frida_assert | MASVS-NETWORK-2, MASVS-RESILIENCE-1 | MASTG-TECH-0012 | **implemented** |
| 7 | IDOR on the Backend | `071-idor-backend` | network_assert | MASVS-AUTH-1 | MASTG-TECH-0011 | **implemented** |
| 7 | Broken Auth / Token Forgery | `072-broken-auth-token-forgery` | network_assert | MASVS-AUTH-1, MASVS-AUTH-2 | MASTG-TECH-0011 | **implemented** |
| 8 | Exported Component / Deep Link Abuse | `081-exported-component-deeplink` | flag | MASVS-PLATFORM-1 | MASTG-TECH-0029 | **implemented** |
| 8 | WebView JS-Bridge Exploit | `082-webview-jsbridge-exploit` | static_assert | MASVS-PLATFORM-2 | MASTG-TECH-0030 | **implemented** |
| 8 | Leaky Content Provider | `083-leaky-content-provider` | flag | MASVS-PLATFORM-3 | MASTG-TECH-0031 | **implemented** |
| 8 | Confused-Deputy Privilege Re-Delegation | `084-confused-deputy-privesc` | flag | MASVS-PLATFORM-1 | MASTG-TECH-0029 | **implemented** |
| 9 | ⭐ Root Detection Bypass | `009-root-detection-bypass` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0144 | **implemented** |
| 9 | Anti-Frida / Anti-Debug Evasion | `091-anti-frida-anti-debug` | frida_assert | MASVS-RESILIENCE-2, MASVS-RESILIENCE-3 | MASTG-TECH-0043 | **implemented** |
| 9 | Defeat Integrity/Tamper Check | `092-defeat-integrity-check` | flag | MASVS-RESILIENCE-4 | MASTG-TECH-0049 | **implemented** |
| 9 | Emulator / Sandbox Detection Bypass | `093-emulator-detection-bypass` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0043 | **implemented** |
| 9 | Anti-Debug (TracerPid) Bypass | `094-anti-debug-tracerpid` | frida_assert | MASVS-RESILIENCE-4 | MASTG-TECH-0043 | **implemented** |
| 9 | Defeat String Encryption (Anti-Static-Analysis) | `095-string-encryption-deobf` | static_assert | MASVS-RESILIENCE-3 | MASTG-TECH-0023 | **implemented** |
| 9 | Forge a Play-Integrity / Attestation Verdict | `096-play-integrity-bypass` | frida_assert | MASVS-RESILIENCE-1 | MASTG-TECH-0043 | **implemented** |
| 10 | PII Leaked to a Third-Party SDK | `104-pii-third-party-leak` | static_assert | MASVS-PRIVACY-1 | MASTG-TEST-0206 | **implemented** |
| 11 | Full Chain Capstone | `101-full-chain` | flag | MASVS-STORAGE-1, MASVS-NETWORK-2, MASVS-AUTH-1, MASVS-RESILIENCE-1 | MASTG-TECH-0011 | **implemented** |

## Coverage by MASVS category

| MASVS v2 category | Covered by |
|-------------------|-----------|
| MASVS-STORAGE | Modules 1, 2, 3 |
| MASVS-CRYPTO | Module 3 |
| MASVS-NETWORK | Modules 5, 6 |
| MASVS-AUTH | Module 7 |
| MASVS-PLATFORM | Module 8 |
| MASVS-CODE | Modules 0, 1 |
| MASVS-RESILIENCE | Modules 4, 6, 9, 11 |
| MASVS-PRIVACY | Module 10 |

All 8 MASVS v2 categories are covered.

## Grader-type coverage

| Grader type | Count | Implemented | Reference (live-device) task |
|-------------|:-----:|:-----------:|----------------|
| `flag` | 11 | 11 | recovered-value detection |
| `static_assert` | 7 | 7 | ⭐ `001-find-hardcoded-secret` |
| `network_assert` | 4 | 4 | ⭐ `005-intercept-api-call` |
| `frida_assert` | 8 | 8 | ⭐ `009-root-detection-bypass` |

All 30 tasks pass their own PASS/FAIL detection test in dry-run
(`runner/tests/test_all_tasks_gradeable.py`).

## Module 9 — RASP technique tour

Module 9 is a full Runtime Application Self-Protection technique tour: each major
RASP class is its own task with its own bypass objective, all against the bundled
`vaultbank` target. Every check is a single in-process decision, which is exactly
why each is defeatable — the lesson being that client-side RASP raises the bar but
is not a trust boundary.

| Technique | Task | Bypass |
|-----------|------|--------|
| Root detection | `009-root-detection-bypass` | hook the root verdict |
| Anti-Frida / anti-debug (maps/ports) | `091-anti-frida-anti-debug` | hook the instrumentation check |
| Signature / tamper integrity | `092-defeat-integrity-check` | flip the integrity branch |
| Emulator / sandbox detection | `093-emulator-detection-bypass` | hook `isEmulator()` |
| Debugger detection (ptrace / TracerPid) | `094-anti-debug-tracerpid` | hook `isBeingTraced()` |
| String encryption (anti-static-analysis) | `095-string-encryption-deobf` | replay the XOR decode offline |
| Play-Integrity / attestation stub | `096-play-integrity-bypass` | forge the local verdict |
