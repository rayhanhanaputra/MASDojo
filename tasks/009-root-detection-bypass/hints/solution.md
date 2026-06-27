**Full solution.**

Submit this Frida script:

```js
Java.perform(function () {
    var RootChecker = Java.use("org.masdojo.vaultguard.RootChecker");
    RootChecker.isDeviceRooted.implementation = function () {
        return false;
    };
});
```

The runner spawns `org.masdojo.vaultguard` with your script injected before any
app code runs. `MainActivity` calls `RootChecker.isDeviceRooted()` on startup;
your override forces it to `false`, so the app skips the "rooted device" branch,
unlocks the premium vault, and logs:

```
VaultGuard: MASDOJO_UNLOCK:FLAG{r00t_ch3ck_bypass3d}
```

The grader sees that marker in logcat and passes the task.

**Why this is a finding.** Per MASVS-RESILIENCE-1, client-side root detection is
a speed bump, not a security control: an attacker who controls the device can
rewrite the verdict at runtime. Defenses must assume the check can be bypassed —
combine multiple signals, attest server-side, and never gate genuinely sensitive
operations on a client-only boolean.
