**Full solution.** The provided manifest shows the activity is exported with a `vaultbank://secret` deep link and no caller check, so it could be reached without auth (the deep link is illustrative - you analyse the files, you don't launch it). The decompiled activity XOR-decodes `ENC` with `XOR_KEY` and shows the result. Decode it yourself from your files:
```python
print(bytes(b ^ key for b in bytes.fromhex(ENC)).decode())
```
Submit the `FLAG{...}`. Seeded per learner.
