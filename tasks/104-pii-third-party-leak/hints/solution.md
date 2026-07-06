**Full solution.** Of the startup requests, the one to `in.thirdparty-metrics.example` sends `"u":"<base64(email)>"` — PII shared with a third-party tracker (a data-minimization/privacy violation). Decode:
```python
import base64; print(base64.b64decode(U).decode())
```
Submit the email. Seeded per learner. The app's own `api.vaultbank.example` request and the ad SDK request are decoys — only the tracker leaks PII.
