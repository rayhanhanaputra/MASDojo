**Full solution.** One log line leaks `Authorization: Basic <base64(user:token)>`:
```python
import base64; print(base64.b64decode(B64).decode())   # -> user:tok_...
```
Submit the `tok_…` token. Seeded per learner. Lesson: never log Authorization headers.
