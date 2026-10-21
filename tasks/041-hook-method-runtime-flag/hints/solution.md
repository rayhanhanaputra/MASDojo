**Full solution.**

```js
Java.perform(function () {
  var D = Java.use('org.masdojo.vaultbank.DashboardActivity');
  D.computeReward.implementation = function () {
    var r = this.computeReward();
    send('reward=' + r);
    return r;
  };
});
```

Submit this script. `computeReward()` returns `FLAG{runt1m3_r3w4rd_h00k3d}` at
runtime; because the app only ever logs its length, a runtime hook that reads the
return value is the only way to recover it. **Why this is a finding:** values a
client computes are fully observable to anyone who can instrument the process -
never rely on "it's never shown in the UI" as a secrecy boundary.
