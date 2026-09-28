**Full solution.**

```js
Java.perform(function () {
  var Emu = Java.use('org.masdojo.vaultbank.EmulatorDetector');
  Emu.isEmulator.implementation = function () {
    return false;   // report "physical device" — the reward unlocks
  };
});
```

Launch `.RaspLabActivity` (`adb shell am start -a android.intent.action.VIEW -d "vaultbank://rasplab"`) with the script injected. The dry-run grader statically confirms the hook targets `EmulatorDetector.isEmulator()` and forces `false`; on a KVM host it also verifies `MASDOJO_UNLOCK_EMU:<flag>` appears only after the hook.
