**Full solution.**

```js
Java.perform(function () {
  Java.use('org.masdojo.rasp.AntiTamper').isInstrumented.implementation = function () { return false; };
});
```
Submit it.
