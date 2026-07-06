**Full solution.**

On the emulator, `adb shell run-as <pkg> cat shared_prefs/auth.xml` (or open the `shared_prefs/auth.xml` file in this task) reveals `<string name="auth_token">sk_live_…</string>` in cleartext. Submit that `sk_live_…` value.

This challenge is seeded per learner: your `auth_token` is unique to you, so there is no single shared flag — you must read your own file. That's the point: recovering the secret *is* the proof you performed the technique.
