**Full solution.** The exported provider returns `value` base64-encoded:
```python
import base64; print(base64.b64decode(VALUE).decode())
```
Submit the decoded `FLAG{...}`. (Live: `adb shell content query --uri content://com.vaultbank.provider/secrets`.) Seeded per learner.
