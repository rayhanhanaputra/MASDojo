// Reference solution — NOT shown to the learner.
// Defeats VaultGuard's root detection by forcing RootChecker.isDeviceRooted()
// to return false. Hooking at the boolean choke-point is more robust than
// hiding every individual indicator (su binary, test-keys, etc.).
Java.perform(function () {
    var RootChecker = Java.use("org.masdojo.vaultguard.RootChecker");
    RootChecker.isDeviceRooted.implementation = function () {
        send("hook fired: isDeviceRooted forced to false");
        return false;
    };
});
