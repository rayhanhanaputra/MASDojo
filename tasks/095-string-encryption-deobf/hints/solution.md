**Full solution.** Replay the app's own decode. With `ENC` = the `reward` hex and `KEY` = `XOR_KEY` from your decompiled `StringVault`:

```python
ENC = "..."          # the "reward" ciphertext from YOUR StringVault table
KEY = 0x..           # XOR_KEY from YOUR StringVault
print(bytes(b ^ KEY for b in bytes.fromhex(ENC)).decode())
```

That prints your `FLAG{str1ng_3ncrypt10n_...}`. Submit it. The value is seeded per
learner and never appears in cleartext in the challenge files — recovering it is
proof you reversed the obfuscation.
