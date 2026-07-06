# infra/

Infrastructure and host-side scripts for self-hosting MASDojo.

- `docker-compose.yml` lives in the repo root for one-command bring-up.
- Service Dockerfiles live with each service (`backend/Dockerfile`,
  `frontend/Dockerfile`, `runner/Dockerfile`, `vulnapi/Dockerfile`).

## Scripts

**Local model** (run the platform on your own machine — see [`docs/local-mode.md`](../docs/local-mode.md)):
- `preflight.sh` (`make doctor`) — check the host has everything for the workshop.
- `avd-up.sh` (`make avd-up`) — provision a local rooted AVD + matching frida-server.
- `avd-check.sh` (`make avd-check`) — confirm the AVD is ready for live grading.

**Container/KVM model** (baked into the runner image, see [`docs/deploy-kvm.md`](../docs/deploy-kvm.md)):
- `avd/setup-sdk.sh`, `avd/create-avd.sh` — invoked from `runner/Dockerfile` to
  install the Android SDK + create the AVD the runner boots.
- `avd/push-frida.sh`, `avd/install-mitm-ca.sh` — prepare the booted device.

**Apps & CI**:
- `build-apps.sh` (`make apps`) — build the intentionally-vulnerable target APKs.
- `ci/live_grade.sh` — the KVM live-grade CI step.

## Runner host requirements

- Linux host with `/dev/kvm` (the compose `runner` service maps it in), or run
  the runner on your host in attach mode against a local AVD (`make runner-host`).
- Android SDK command-line tools: `sdkmanager`, `avdmanager`, `emulator`, `adb`.
- `frida-tools` matching the `FRIDA_VERSION` pushed to the device.
- `mitmproxy` for `network_assert` capture.
