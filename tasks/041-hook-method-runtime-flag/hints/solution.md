**Full solution.**

```js
Java.perform(function () {
  var F = Java.use('org.masdojo.hooklab.Flagger');
  F.computeFlag.implementation = function () {
    var r = this.computeFlag();
    send('flag=' + r);
    return r;
  };
});
```
Submit this script.
