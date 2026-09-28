**Full solution.** The exported, unguarded `GrantReceiver` mints an elevation grant for any caller (confused deputy). Reconstruct the grant it returns by replaying its own `decodeGrant()` on your seeded `ENC` / `GRANT_KEY`:

```python
ENC = "..."          # from YOUR decompiled GrantReceiver
KEY = 0x..           # GRANT_KEY from YOUR decompiled GrantReceiver
print(bytes(b ^ KEY for b in bytes.fromhex(ENC)).decode())
```

On a device you could instead read it live from the ordered-broadcast result or
logcat (`MASDOJO_UNLOCK:<grant>`) after sending the broadcast. Submit the
`FLAG{c0nfus3d_d3puty_...}`. The value is seeded per learner, so it can't be
shared. The fix: guard the receiver with a signature-level permission and verify
the caller — or don't export a privilege-granting action at all.
