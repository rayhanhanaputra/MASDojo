**Full solution.**

```python
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
ct = base64.b64decode(open('artifacts/weak.enc').read())
d = Cipher(algorithms.AES(b'masdojo_ecb_key!'), modes.ECB()).decryptor()
pt = d.update(ct) + d.finalize()
print(pt[:-pt[-1]].decode())
```
→ `FLAG{3cb_l3aks_th3_p3ngu1n}`. Submit the plaintext.
