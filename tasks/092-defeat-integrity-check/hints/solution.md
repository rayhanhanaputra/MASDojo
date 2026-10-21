**Full solution.**

```js
Java.perform(function () {
  var I = Java.use('org.masdojo.vaultbank.IntegrityChecker');
  I.isValidSignature.implementation = function (ctx) { return true; };
});
```

Submit this script. At baseline the signature check fails and the app logs
`MASDOJO_DENIED_INTEGRITY`; with the hook `isValidSignature()` returns true and the
app reveals `MASDOJO_UNLOCK_INTEGRITY:FLAG{s1gn4tur3_ch3ck_d3f34t3d}`. **Why this
is a finding:** a tamper/integrity check that runs inside the app it protects can
always be hooked or patched out - it raises effort, not a real boundary. Pair it
with server-side attestation if you need assurance.
