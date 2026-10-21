**Full solution.** The exported provider returns `value` base64-encoded:
```python
import base64; print(base64.b64decode(VALUE).decode())
```
Submit the decoded `FLAG{...}`. (The `content query` an attacker app would run against this exported provider is illustrative of the leak; you decode the value from the provided `provider_dump.txt`, not from a live query.) Seeded per learner.
