**Full solution.**

```js
Java.perform(function () {
  var CP = Java.use('okhttp3.CertificatePinner');
  CP.check.overload('java.lang.String', 'java.util.List').implementation = function () { return; };
});
```
Submit this bypass script.
