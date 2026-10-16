# Visual emulator in the interactive lab

The interactive lab gives every learner an in-browser **terminal** (adb / frida /
jadx / apktool, in an isolated workstation container - see
[`local-mode.md`](local-mode.md) and the `lab` compose profile). On a KVM runner
with a live emulator you can also give them a **visual device screen** (see and
tap the emulator) next to the terminal.

The frontend already has the "device screen" tab. It embeds whatever URL the
backend reports in `LAB_STREAM_URL`; when that is empty it shows a clear "no
device screen" message and the terminal keeps working. `%(serial)s` in the URL
is replaced with the session's device serial.

This is **KVM-gated**: it needs a real/emulated Android device reachable over
adb, so it is set up on the runner host, not on a laptop-only install.

## Option A - scrcpy over the web (any adb device)

[`ws-scrcpy`](https://github.com/NetrisTV/ws-scrcpy) streams an adb device's
screen (with touch/keyboard input) to the browser. On the runner host:

```bash
# with the emulator already booted and visible to `adb devices`
docker run -d --name ws-scrcpy --network host netris/ws-scrcpy   # or build from source
```

Then point the backend at it:

```
LAB_STREAM_URL=http://<runner-host>:8000/#!action=stream&udid=%(serial)s
```

## Option B - Android emulator WebRTC (emulator-native)

The emulator exposes a gRPC endpoint; Google's
[`android-emulator-webrtc`](https://github.com/google/android-emulator-container-scripts)
component streams it to the browser via grpc-web through an Envoy proxy. Boot the
emulator with `-grpc <port>`, run the Envoy + token service from that project,
and set:

```
LAB_STREAM_URL=https://<runner-host>:<webrtc-port>/
```

## Security notes

- The stream service must be reachable by the learner's browser but should sit
  behind the same auth/proxy as the rest of the deployment.
- The visual view is an addition to, not a replacement for, the isolated
  terminal container - it never exposes backend secrets.
- Leave `LAB_STREAM_URL` empty for CLI-only installs (the default).
