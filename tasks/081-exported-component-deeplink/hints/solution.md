**Full solution.** The activity is exported (manifest) and reachable without auth via `am start -d "vaultbank://secret"`. It XOR-decodes `ENC` with `XOR_KEY` and shows the result. Decode it yourself:
```python
print(bytes(b ^ key for b in bytes.fromhex(ENC)).decode())
```
Submit the `FLAG{...}`. Seeded per learner.
