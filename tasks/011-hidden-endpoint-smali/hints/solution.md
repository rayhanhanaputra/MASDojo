**Full solution.** `DebugApi.adminUrl()` decodes `ENC` by XOR-ing each byte with `XOR_KEY`. Reproduce it:
```python
print(bytes(b ^ key for b in bytes.fromhex(ENC)).decode())
```
Submit the recovered `/internal/v1/admin/...` path. Seeded per learner — no shared answer.
