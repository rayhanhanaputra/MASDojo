# Deploying MASDojo on a KVM host (full emulator grading)

The database, Redis, backend, and frontend run anywhere Docker runs — including
your Mac. The **runner** is different: it boots a real Android emulator, which
needs hardware virtualization (`/dev/kvm`). This guide gets the *full* stack,
including live emulator grading of the reference tasks, running on a Linux host
with KVM.

## 1. Pick a host that actually exposes /dev/kvm

> ⚠️ **DigitalOcean standard droplets do NOT support nested virtualization** —
> there is no `/dev/kvm`, so the Android emulator can't boot there. Same for most
> "cloud VM" products (Linode, Vultr cloud compute, Hetzner Cloud, plain EC2/GCE
> instances). You need one of:

**Bare metal (real KVM, best price/perf — recommended):**

| Provider | Product | Notes |
|----------|---------|-------|
| **Hetzner** | Dedicated / Server Auction | Cheapest solid option (~€35–45/mo). EU + US. |
| OVHcloud / So you Start / Kimsufi | Dedicated | Cheap bare metal. |
| Vultr | **Bare Metal** | Hourly billing, quick to spin up. |
| Scaleway | Elastic Metal | EU. |
| Equinix Metal / Latitude.sh | Bare Metal | Global, hourly. |

**Cloud VMs that *do* expose nested virtualization:**

| Provider | How |
|----------|-----|
| **Google Cloud (GCE)** | Intel Haswell+; create with `--enable-nested-virtualization`. New users get free credit — easiest cloud path. |
| AWS | Only `*.metal` instances (e.g. `c5.metal`) give real KVM. |
| Azure | Some `Dv3`/`Ev3` sizes support nested virtualization. |

**Recommended:** a **Hetzner bare-metal** box (cheapest) or **GCE with nested
virtualization** (easiest, free credits).

### Host spec
- x86_64, **≥4 vCPU, ≥8 GB RAM**, ~30 GB disk
- Ubuntu 22.04 / 24.04
- Verify KVM is present:
  ```bash
  ls -l /dev/kvm && egrep -c '(vmx|svm)' /proc/cpuinfo   # non-zero = good
  ```

## 2. Install Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER" && newgrp docker
```

## 3. Clone and configure

```bash
git clone <your-fork-url> masdojo && cd masdojo
cp .env.example .env
# set fresh secrets:
sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$(openssl rand -hex 32)|" .env
sed -i "s|^MASTER_KEY=.*|MASTER_KEY=$(python3 -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')|" .env
```

## 4. Build the target APKs

The reference tasks need their intentionally-vulnerable APKs built from `apps/`.
Use a throwaway container that has the Android SDK + Gradle (no host install):

```bash
make apps            # or see the raw command below
```

Raw equivalent (what `make apps` runs):

```bash
docker run --rm -v "$PWD":/work -w /work mingc/android-build-box:latest \
  bash infra/build-apps.sh
```

This produces `tasks/00{1,5,9}-*/app/target.apk`. (First run pulls a large image
and downloads Gradle deps — give it a few minutes.)

## 5. Bring up the full stack

```bash
docker compose up --build -d
```

This starts db, redis, backend, frontend, **and** the runner. The runner cold-
boots the AVD and saves a clean snapshot on first start — watch for it:

```bash
docker compose logs -f runner   # wait for "saved AVD snapshot 'masdojo_clean'"
```

## 6. Use it

- Open `http://<host-ip>:5173`, register, and work the reference tasks.
- Submit the hardcoded secret for task 001, the Frida bypass for 009, or the
  intercepted token for 005 — each grades on the real emulator and returns
  PASS/FAIL with evidence.

> For a public host, put the frontend/backend behind a reverse proxy with TLS
> (Caddy/nginx) and restrict the db/redis ports; the compose file publishes them
> for convenience in local/dev use.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| runner: `KVM required` / emulator won't boot | Host has no `/dev/kvm` — wrong provider (see step 1). |
| submissions stay `queued` | runner not running or not consuming; `docker compose logs runner`. |
| `network_assert` task never captures | the bundled mock backend or proxy didn't start; check runner logs. |
| Want to grade without an emulator | set `RUNNER_DRY_RUN=true` — grades `flag`/`static_assert` only. |
