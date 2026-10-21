**Full solution.**

```js
Java.perform(function () {
  var F = Java.use('org.masdojo.vaultbank.FeatureGate');
  F.isUnlocked.implementation = function () { return true; };
});
```

Submit this script. At baseline the gate logs `MASDOJO_DENIED_FEATURE`; with the
hook, `isUnlocked()` returns true and the app reveals
`MASDOJO_UNLOCK_FEATURE:FLAG{f34tur3_g4t3_fl1pp3d}`. **Why this is a finding:** an
entitlement decision made entirely on the client is one boolean away from being
bypassed - gate premium features server-side.
