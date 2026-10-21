**Full solution.** The exported, unguarded `GrantReceiver` mints an elevation grant for any caller (confused deputy). Reconstruct the grant it returns by replaying its own `decodeGrant()` on your seeded `ENC` / `GRANT_KEY`:

```python
ENC = "..."          # from YOUR decompiled GrantReceiver
KEY = 0x..           # GRANT_KEY from YOUR decompiled GrantReceiver
print(bytes(b ^ KEY for b in bytes.fromhex(ENC)).decode())
```

Reconstruct the grant from the `ENC` / `GRANT_KEY` in *your own* seeded
`decompiled/GrantReceiver.java` and submit the `FLAG{c0nfus3d_d3puty_...}`. The
value is seeded per learner, so it can't be shared - recover it statically from
your artifact rather than from a device. The fix: guard the receiver with a
signature-level permission and verify the caller - or don't export a
privilege-granting action at all.
