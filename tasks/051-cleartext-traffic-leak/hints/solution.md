**Full solution.** Only the `POST http://…/v1/login` goes in cleartext (the rest are HTTPS). Its body carries `"password":"<base64>"`:
```python
import base64; print(base64.b64decode(PW).decode())
```
Submit the `cred_…` value. Seeded per learner. Lesson: cleartext HTTP exposes everything; base64 in the body is not protection.
