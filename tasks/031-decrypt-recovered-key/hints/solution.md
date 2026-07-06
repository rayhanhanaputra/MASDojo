**Full solution.**

```python
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
blob = base64.b64decode(open('artifacts/secret.enc').read())
iv, ct = blob[:16], blob[16:]
key = bytes.fromhex('8f3c1d77a94b42e0b6c5e9f0a1d2c3b4')
d = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
pt = d.update(ct) + d.finalize()
print(pt[:-pt[-1]].decode())
```
→ `FLAG{d3crypt_w1th_r3c0v3r3d_k3y}`. You can only get this by actually decrypting — submit it.
