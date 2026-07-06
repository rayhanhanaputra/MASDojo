**Full solution.**

`adb logcat | grep -i token` (or reading your `logcat.txt`) surfaces `AuthManager: issuing session for <user> token=sess_…`. Submit that `sess_…` value. The token is uniquely seeded to you — there is no shared flag, so you must read your own dump.
