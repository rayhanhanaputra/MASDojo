# Local single-participant mode (workshop / self-hosted-on-your-laptop)

MASDojo can run entirely on one participant's machine — no cloud, no KVM VM, no
accounts. The participant's own laptop provides the virtualization for the
Android emulator, and the grader attaches to that local AVD.

This is the recommended model for a workshop: it tolerates weak venue wifi (all
local), costs nothing, and needs no shared infrastructure.

## What runs where

```
Your laptop:
  docker compose:  db + redis + backend + frontend + vulnapi   (make solo)
  runner:          on the HOST, attach mode                     (make runner-host)
  AVD:             local, rooted + frida-server                 (make avd-up)
```

## One-time setup

Install the toolchain: Android SDK (`sdkmanager`, `avdmanager`, `emulator`,
`adb`) with `ANDROID_SDK_ROOT` set, `curl`, `xz`, and Python for the host runner.
Hardware virtualization must be enabled (Apple Silicon / Intel VT-x / AMD-V).

## Run it

```bash
make solo         # stack in solo mode -> http://localhost:5173 (no login)
                  # Lab 3 vulnerable API -> http://localhost:8091
```

That alone covers Lab 1 (RE/secrets, static + seeded) and Lab 3 (API abuse) —
neither needs an emulator. For Lab 2 (live Frida/RASP grading):

```bash
make avd-up       # create a rooted AVD + push/launch a matching frida-server
make avd-check    # pre-flight: confirm the AVD is online, booted, frida running
make runner-host  # run the grader on your host, attached to the local AVD
```

- `avd-up` picks the right emulator ABI + frida-server arch for your host
  (arm64 on Apple Silicon, x86_64 on Intel/Linux) and uses a `google_apis`
  image so `adb root` works.
- `runner-host` runs with `RUNNER_ATTACH=true`: it attaches to the AVD you
  provisioned, grades against it, and never boots or shuts down your device.

## Why no login

`SOLO_MODE=true` (set by `make solo`) resolves a single implicit local profile —
the UI skips login and drops straight into the curriculum. Seeded challenges
stay per-participant via `INSTALL_SALT` (a random value `make env` writes), so
even with one profile each machine gets different targets and answers can't be
shared. For a shared multi-user deployment, leave `SOLO_MODE=false` (the JWT
auth path is unchanged).

## Notes / caveats

- Baseline root is `adb root` on the `google_apis` image — enough to run
  frida-server and defeat the curriculum's root-detection tasks. Magisk-grade
  root (via rootAVD) is only needed for challenges that require a real `su`
  binary; add it separately if you author such a task.
- Windows: run the stack under WSL2; the emulator + adb are smoothest on
  Mac/Linux.
- Attach mode grades against live device state (no per-job snapshot restore).
  For a single participant working sequentially this is fine; the shared,
  snapshot-isolated path is the KVM deployment (see `deploy-kvm.md`).
