**Full solution.** `qa_unlock_note` in `strings.xml` is a base64-encoded flag:
```python
import base64; print(base64.b64decode(VALUE).decode())
```
Submit the decoded `FLAG{...}`. Seeded per learner. Lesson: resources hide secrets, and base64 is not secrecy.
