# Local single-participant mode (workshop / self-hosted-on-your-laptop)

MASDojo can run entirely on one participant's machine - no cloud, no KVM VM, no
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

That alone covers Lab 1 (RE/secrets, static + seeded) and Lab 3 (API abuse) -
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

`SOLO_MODE=true` (set by `make solo`) resolves a single implicit local profile -
the UI skips login and drops straight into the curriculum. Seeded challenges
stay per-participant via `INSTALL_SALT` (a random value `make env` writes), so
even with one profile each machine gets different targets and answers can't be
shared. For a shared multi-user deployment, leave `SOLO_MODE=false` (the JWT
auth path is unchanged).

## Notes / caveats

- Baseline root is `adb root` on the `google_apis` image - enough to run
  frida-server and defeat the curriculum's root-detection tasks. Magisk-grade
  root (via rootAVD) is only needed for challenges that require a real `su`
  binary; add it separately if you author such a task.
- Windows: run the stack under WSL2; the emulator + adb are smoothest on
  Mac/Linux.
- Attach mode grades against live device state (no per-job snapshot restore).
  For a single participant working sequentially this is fine; the shared,
  snapshot-isolated path is the KVM deployment (see `deploy-kvm.md`).

## macOS (Apple Silicon): live grading without KVM

KVM is a Linux-only kernel feature (`/dev/kvm`), so the dockerized `runner`
service never starts on a Mac. That does **not** mean the Mac can't run an
emulator - it runs one natively via Apple's Hypervisor.framework. Use the
host-runner (attach) path instead of the KVM runner:

```bash
make solo                 # db + redis + backend + frontend in Docker (no runner)
make avd-up               # native rooted AVD + frida-server (uses the Android SDK)
make runner-host          # runner on the host, attached to the native emulator
```

Two gotchas seen on Apple Silicon:

- **Frida versions must match exactly.** The client (the host runner's
  `frida` and the lab container's `frida-tools`) and the device's
  `frida-server` must be the same version, or injection fails. `make avd-up`
  pins a known server; if you install a newer client, push the matching
  `frida-server-<version>-android-arm64` to `/data/local/tmp/frida-server`.
- **A native Postgres/Redis on the default port shadows the Docker one.** If you
  also run a local Postgres on `5432`, `localhost:5432` hits *it*, not the
  container (whose role won't exist). Point the host runner at the Mac's LAN IP
  (`ipconfig getifaddr en0`) instead of `localhost` in `DATABASE_URL` /
  `REDIS_URL`, or remap the container's published ports.

The visual emulator view is free here: the native emulator already shows a
window. The in-browser "device screen" tab (`LAB_STREAM_URL`, see
`lab-visual.md`) is for headless hosted runners.

### adb / frida in the browser lab terminal (against the native emulator)

The isolated lab container (`--profile lab`) ships an arch-native `adb` and
`frida`. To let them drive the Mac's native emulator, expose the host's adb
server on all interfaces once, then the container reaches it via
`ADB_SERVER_SOCKET` (already set in compose to `host.docker.internal:5037`):

```bash
adb kill-server
adb -a -P 5037 nodaemon server &   # listen on all interfaces so the container can connect
docker compose --profile lab up -d --build lab
```

Then in the in-browser terminal: `adb devices`, `adb -s emulator-5554 shell`,
`frida-ps -D emulator-5554`, etc. all work against the live rooted device.
(Google's platform-tools `adb` is x86_64-only, so the image uses the distro's
`android-tools-adb` to run on arm64.)
