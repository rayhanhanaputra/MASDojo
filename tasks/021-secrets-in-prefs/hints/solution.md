**Full solution.** The token is base64 in shared_prefs:
```python
import base64; print(base64.b64decode(VALUE).decode())
```
Submit the `sk_live_…` token. Seeded per learner — no shared answer. Lesson: base64 in local storage is still cleartext storage of a secret.
