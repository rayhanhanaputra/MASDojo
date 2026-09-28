**Full solution.**

```js
Java.perform(function () {
  var Dbg = Java.use('org.masdojo.vaultbank.DebugDetector');
  Dbg.isBeingTraced.implementation = function () {
    return false;   // claim "no tracer" no matter what /proc/self/status says
  };
});
```

The Java-layer hook is enough because the app funnels the whole decision through
`isBeingTraced()`. (A deeper alternative: intercept the `TracerPid:` read so it
always parses 0 — useful when the check is inlined in native code.) The dry-run
grader confirms the hook targets `DebugDetector.isBeingTraced()` and forces
`false`; on a KVM host it also checks for `MASDOJO_UNLOCK_DBG:<flag>`.
