**Full solution.** `verify()` guards the reward behind a signature check; flipping the `if-eqz v0, :tampered` branch reaches the valid path, which returns the XOR-decoded reward:
```python
print(bytes(b ^ key for b in bytes.fromhex(ENC)).decode())
```
Submit the `FLAG{...}`. Seeded per learner.
