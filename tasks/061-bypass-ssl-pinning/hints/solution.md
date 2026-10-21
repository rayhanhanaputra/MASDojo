**Full solution.**

```js
Java.perform(function () {
  var CP = Java.use('okhttp3.CertificatePinner');
  CP.check.overload('java.lang.String', 'java.util.List').implementation = function (host, certs) {
    // Pinning defeated: accept any certificate chain.
  };
});
```

Submit this script. At baseline `CertificatePinner.check()` throws (the presented
cert doesn't match the pin) and the app logs `MASDOJO_DENIED_PIN`; with the hook
it returns normally and the app logs
`MASDOJO_UNLOCK_PIN:FLAG{ssl_p1nn1ng_d3f34t3d}`. In a real assessment this is what
lets your proxy CA be accepted so you can read the "protected" traffic. **Fix:**
pinning raises the bar but is defeated by instrumentation - treat the client as
untrusted and enforce auth server-side.
