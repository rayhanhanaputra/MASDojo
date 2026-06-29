**Full solution.**

1. The decoded app is in `artifacts/`. Read the manifest:
   ```bash
   cat tasks/000-apk-anatomy-recon/artifacts/AndroidManifest.xml
   ```
   Note it declares `INTERNET` + `READ_CONTACTS`, is `debuggable="true"`, and
   has an **exported** `DebugActivity` with no permission guard (foreshadowing
   Module 8).
2. Recover the flag from the resources:
   ```bash
   grep -rn "FLAG{" tasks/000-apk-anatomy-recon/artifacts/res/
   ```
   It lives in `res/values/strings.xml` as `qa_unlock_note`:
   ```
   FLAG{4pk_r3con_c0mpl3t3}
   ```
   Submit that in the **value** field.

**Why this matters.** Per MASVS-CODE, treat the APK as fully transparent —
strings, resources, the manifest, and debug flags all ship to every device.
`apktool d` makes this trivial. Never store anything in resources you wouldn't
hand directly to an attacker.
