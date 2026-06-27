# MASDojo Demo Script

A ~5-minute walkthrough for Black Hat Arsenal / DEF CON Demo Labs. Pre-build the
images and pre-boot the AVD snapshot so grading is snappy on stage.

> **GIF/screenshot slot:** capture this flow into `docs/assets/demo.gif` and link
> it from the README's screenshot slot before submission.

## Setup (before the talk)

```bash
cp .env.example .env
# set JWT_SECRET and MASTER_KEY to fresh random values
docker compose up --build -d        # db, redis, backend, frontend, runner
infra/build-apps.sh                 # build the three reference target APKs
```

Confirm the runner booted the AVD and saved its clean snapshot (runner logs:
"saved AVD snapshot 'masdojo_clean'").

## The pitch (30s)

> "Most security training grades you on the honor system. MASDojo grades you on a
> real Android emulator. When you think you've solved a task, it boots a device,
> installs the vulnerable app, applies your exploit, and tells you PASS or FAIL
> with evidence. It's self-hosted, MASVS/MASTG-aligned, and the AI mentor is
> bring-your-own-key — so it's free to run."

## The flow

1. **Register** a fresh account → land on the **skill map**. Point out the
   prerequisite DAG: most tasks are locked; module 0 is the entry point. Note the
   recommended-next card.

2. **Static (`001` ⭐ Find the Hardcoded API Secret).** In a terminal:
   ```bash
   jadx -d /tmp/sn tasks/001-find-hardcoded-secret/app/target.apk
   grep -rn "msd_live_sk_" /tmp/sn
   ```
   Paste the recovered key into the task's submit box → **PASS**, with the two
   checks (matches the secret / genuinely embedded in the APK). Show the score
   reflecting that no hints were used.

3. **Frida (`009` ⭐ Root Detection Bypass).** Paste the bypass script:
   ```js
   Java.perform(function () {
     Java.use("org.masdojo.vaultguard.RootChecker")
         .isDeviceRooted.implementation = function () { return false; };
   });
   ```
   Submit → the runner spawns the app with the hook injected → **PASS**: the vault
   unlocked and logged the flag. Emphasise this ran on a real device.

4. **Network (`005` ⭐ Intercept & Capture the API Call).** Submit the device
   token captured from the telemetry request → the runner proxies the emulator
   through mitmproxy, triggers the app, and confirms the captured value → **PASS**.

5. **AI mentor (BYOK).** Open **Settings**, paste an Anthropic/OpenAI key (Test &
   Save → masked, encrypted at rest). Back in a task, hit **✦ AI hint** to show the
   Socratic, tier-aware hint, and **Explain this** on a smali snippet. Note: no
   key → features hidden, grader still works.

6. **Profile.** Show domain mastery bars and the score, driven by hints used and
   attempts.

## Close (15s)

> "Three reference tasks prove all four grader types end to end; the rest of the
> ten-module curriculum is scaffolded and ready to fill in. Apache-2.0, one command
> to stand up. Add your own tasks with `tasks/_template/`."
