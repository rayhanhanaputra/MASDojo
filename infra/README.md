# infra/

Infrastructure for self-hosting MASDojo.

- `docker-compose.yml` lives in the repo root for one-command bring-up.
- Service Dockerfiles live with each service (`backend/Dockerfile`, `frontend/Dockerfile`, `runner/Dockerfile`).
- `avd/` — scripts to provision the Android SDK + AVD image the runner boots (added in milestone 3).

## Runner host requirements

The runner boots a real Android emulator and needs hardware virtualization:

- Linux host with `/dev/kvm` (the compose `runner` service maps it in).
- Android SDK command-line tools: `sdkmanager`, `avdmanager`, `emulator`, `adb`.
- `frida-tools` (client) matching the `FRIDA_VERSION` pushed to the device.
- `mitmproxy` for `network_assert` capture.

If KVM can't be exposed to containers, run the runner on bare metal — see `docs/architecture.md#runner-on-bare-metal`.
