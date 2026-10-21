**Full solution.** Decompile, flip the premium boolean, repack, re-sign, and
upload the patched build:

```bash
apktool d MASDojo.apk -o vb
# In vb/smali*/org/masdojo/vaultbank/DashboardActivity.smali, isPremiumUser():
#   const/4 v0, 0x0   ->   const/4 v0, 0x1
apktool b vb -o vb-patched.apk
zipalign -f 4 vb-patched.apk vb-aligned.apk
apksigner sign --ks ~/.android/debug.keystore --ks-pass pass:android vb-aligned.apk
```

Upload `vb-aligned.apk`. The runner installs it, launches the dashboard, and sees
the premium path unlock (`MASDOJO_PREMIUM:FLAG{pr3m1um_g4t3_fl1pp3d}`) — which the
shipped build never logs. The reward it reveals is:

```
FLAG{pr3m1um_g4t3_fl1pp3d}
```

**Why this is a finding (MASVS-RESILIENCE-1):** a feature "disabled" only by a
client-side boolean is one smali edit away from being enabled. Anything of value
must be enforced on the backend - the APK is fully under the attacker's control.
