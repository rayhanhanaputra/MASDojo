# Pre-flight — set up your machine before the workshop

Everything in MASDojo runs on **your own laptop**. Do this **before** the session
so we spend class time hacking, not installing. Budget ~30–45 min the first time.

> One-command check at any point: **`make doctor`** — it tells you exactly what's
> missing and how to fix it.

## 0. Machine requirements

- **Hardware virtualization enabled** (Apple Silicon, or Intel VT-x / AMD-V) —
  required for the Android emulator.
- **16 GB RAM recommended** (8 GB works but is tight with emulator + Docker).
- **~40 GB free disk.**
- OS: **macOS, Linux, or Windows (WSL2)**. Mac/Linux are smoothest.
- Admin/sudo rights to install tools and run Docker + the emulator.

## 1. Install the toolchain

### Required (platform + live grading)
| Tool | macOS | Linux (Debian/Ubuntu) | Windows |
|------|-------|-----------------------|---------|
| Docker | Docker Desktop | `docker.io` + compose plugin | Docker Desktop + WSL2 |
| Python 3.11+ | `brew install python` | `apt install python3 python3-venv` | in WSL2 |
| curl, xz | preinstalled / `brew install xz` | `apt install curl xz-utils` | in WSL2 |
| Android SDK | Android Studio **or** cmdline-tools | same | Android Studio |
| Java (for jadx) | `brew install openjdk@17` | `apt install openjdk-17-jre` | winget/OpenJDK |

Set **`ANDROID_SDK_ROOT`** to your SDK path and put its tools on `PATH`:

```bash
export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"      # macOS Android Studio
# Linux Android Studio: $HOME/Android/Sdk
export PATH="$ANDROID_SDK_ROOT/platform-tools:$ANDROID_SDK_ROOT/emulator:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
```

Install the SDK bits (once):
```bash
sdkmanager "platform-tools" "emulator" "cmdline-tools;latest"
```

### Recommended (you'll use these to solve the labs)
```bash
pip install frida-tools objection      # dynamic instrumentation + runtime toolkit
# jadx (APK decompiler): brew install jadx  |  apt install jadx  |  or GitHub release
```

## 2. Get MASDojo and verify

```bash
git clone <repo-url> masdojo && cd masdojo
make doctor        # ✓/✗ for every requirement, with fixes
```

Fix anything red, then re-run `make doctor` until it's all green.

## 3. Bring up the platform (browser-only labs)

```bash
make solo          # http://localhost:5173  (no login — straight into the curriculum)
```
This already gives you **Lab 1** (reverse-engineering & secrets) and **Lab 3**
(API abuse against the bundled vulnerable API at `http://localhost:8091`) —
neither needs an emulator.

## 4. Prepare the emulator (for Lab 2 — live Frida/RASP)

```bash
make avd-up        # creates a rooted AVD + launches a matching frida-server
make avd-check     # confirms it's online, booted, frida running
make runner-host   # runs the grader on your host, attached to the local AVD
```

When `make avd-check` prints **Ready**, you're set for the workshop.

---

## Troubleshooting

**`make doctor` says `adb`/`emulator`/`sdkmanager` missing** — `ANDROID_SDK_ROOT`
isn't set or its tool dirs aren't on `PATH`. See the export lines in step 1.

**`sdkmanager` licenses error** — accept them: `yes | sdkmanager --licenses`.

**Emulator won't boot / is extremely slow** — hardware virtualization is off or
unavailable. macOS: no action on Apple Silicon. Linux: ensure `/dev/kvm` exists
(`ls -l /dev/kvm`) and your user is in the `kvm` group. Windows: enable WHPX and
run under WSL2.

**`avd-up` fails downloading frida-server** — you're offline or behind a proxy.
Pre-download `frida-server-<ver>-android-<arch>.xz` from the Frida GitHub
releases and re-run; the version is `FRIDA_VERSION` (default 16.4.8).

**`frida-ps -U` / grading can't see frida** — the frida-server version must match
your `frida-tools`. Align them, or re-run `make avd-up` (it uses the pinned
version). Confirm it's running: `adb shell pidof frida-server`.

**`adb root` says "cannot run as root"** — you created a `google_play` AVD.
`avd-up` uses a `google_apis` image (rootable); recreate with `make avd-up`.

**Port already in use (5173 / 8000 / 8091 / 5432 / 6379)** — stop whatever's
using it, or `make down` a previous MASDojo, then bring it back up.

**Windows quirks** — run the whole stack inside WSL2. The emulator is happiest
launched from WSL2 with nested virtualization on, or run adb/emulator on the
Windows host and point `ANDROID_SDK_ROOT` at it.

Still stuck? Bring the output of `make doctor` to the setup channel before the
session.
