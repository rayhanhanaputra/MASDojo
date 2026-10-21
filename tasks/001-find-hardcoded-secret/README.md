# 001 - Find the Hardcoded API Secret  ⭐ reference task

**Grader type:** `static_assert` · **MASVS:** MASVS-STORAGE-1

## The vulnerability
The **same** hardcoded API key ships in the learner-facing all-in-one target
`apps/vaultbank` (`org.masdojo.vaultbank`: `BuildConfig.API_KEY` + `ApiConfig`)
**and** in the dedicated `apps/securenotes` (`org.masdojo.securenotes`:
`BuildConfig.API_KEY` + `ApiClient.kt`). Both embed the identical literal, so it
is recoverable by decompilation either way. The learner downloads and analyses
`MASDojo.apk` (vaultbank); the committed grader artifact is `securenotes`'s
`target.apk` (same key), so the two always agree.

## How the grader proves it
The learner submits the recovered key. `grader/grade.py`:
1. compares it (constant-time) against the true secret in `grader/expected.json`, and
2. when the APK is present, confirms the key bytes genuinely appear in `target.apk`.
   An APK's `classes*.dex` is stored *deflated* inside the zip, so the check
   decompresses each entry before scanning (scanning the raw file missed the key
   and failed every correct answer — the original bug).

## Rebuilding the target
```bash
infra/build-apps.sh securenotes
# produces tasks/001-find-hardcoded-secret/app/target.apk
```
The embedded key is defined in `apps/securenotes/app/build.gradle.kts`
(`buildConfigField`) and `ApiClient.kt`; keep it in sync with
`grader/expected.json`.
