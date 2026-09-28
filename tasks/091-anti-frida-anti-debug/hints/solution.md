**Full solution.**

```js
Java.perform(function () {
  Java.use('org.masdojo.vaultbank.AntiTamper').isInstrumented.implementation = function () { return false; };
});
```
Submit it.
