# 084-confused-deputy-privesc — Confused-Deputy Privilege Re-Delegation

**Grader type:** `flag` (seeded) · **MASVS:** MASVS-PLATFORM-1 · **MASTG:** MASTG-TECH-0029 · status: **implemented**

## The vulnerability
`org.masdojo.vaultbank.GrantReceiver` (in `apps/vaultbank`) is a "privilege
helper" `BroadcastReceiver` exported with **no `android:permission`** and no
caller verification. Its `onReceive()` performs a privileged action — minting an
elevation grant that unlocks the admin capability — for *whoever* sends the
`org.masdojo.vaultbank.action.ELEVATE` intent. A lower-privileged caller (another
app, or `adb shell am broadcast`) can therefore obtain an effect it should never
have: the app re-delegates its own privilege to the caller. This is a userland
confused-deputy / permission re-delegation local escalation, confined entirely to
the training app — no kernel, no CVE, no real privilege boundary crossed.

The secure version guards the receiver with a signature-level permission and
checks the caller, or simply does not export a privilege-granting action.

## How the grader proves it
The challenge is seeded per-learner (`challenge/generate.py`): the learner gets
the manifest entry (proving the receiver is exported and unguarded) and the
decompiled receiver, whose grant token is XOR-obfuscated with a per-seed key.
`grader/grade.py` (`grade_seeded_recovered`) regenerates that learner's grant and
constant-time compares. The grant never appears in cleartext in the challenge
files, so recovering it is proof the learner understood the confused-deputy path
and reconstructed the value.

On a KVM host / real AVD the same effect is observable live:
```bash
adb shell am broadcast -a org.masdojo.vaultbank.action.ELEVATE \
  --es requester attacker org.masdojo.vaultbank
adb logcat -s VaultBank   # MASDOJO_GRANT / MASDOJO_UNLOCK:<grant>
```

## Rebuilding the target
```bash
infra/build-apps.sh vaultbank
```
