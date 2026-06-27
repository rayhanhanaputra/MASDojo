# 001 — Find the Hardcoded API Secret  ⭐ reference task

**Grader type:** `static_assert` · **MASVS:** MASVS-STORAGE-1

## The vulnerability
`apps/securenotes` hardcodes its backend API key both as a `BuildConfig` field
(`API_KEY`) and as a constant in `ApiClient.kt`. The key ships inside the APK
and is trivially recoverable by decompilation.

## How the grader proves it
The learner submits the recovered key. `grader/grade.py`:
1. compares it (constant-time) against the true secret in `grader/expected.json`, and
2. when the APK is present, confirms the key bytes genuinely appear in `target.apk`
   (so guessing the format alone can't pass).

## Rebuilding the target
```bash
infra/build-apps.sh securenotes
# produces tasks/001-find-hardcoded-secret/app/target.apk
```
The embedded key is defined in `apps/securenotes/app/build.gradle.kts`
(`buildConfigField`) and `ApiClient.kt`; keep it in sync with
`grader/expected.json`.
