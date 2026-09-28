# MASDojo — Mobile App Security Dojo

> A self-hostable platform for learning Android app penetration testing. Every
> task ships with an automated grader that checks you actually applied the
> technique — not that you guessed a flag.

![CI](https://github.com/rayhanhanaputra/MASDojo/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)

MASDojo builds a hands-on curriculum on top of the OWASP MASVS / MASTG body of
knowledge. Each task pairs a deliberately vulnerable target app with an objective
and a grader. You submit what the task asks for — a recovered secret, a Frida
script, or a captured request — and the grader returns pass or fail with the
individual checks it ran, so you can see exactly what held and what didn't.

Device-backed tasks run against a real Android emulator: the runner restores an
AVD snapshot, installs the target APK, applies your submission, and grades the
result. Most tasks also grade in dry-run from committed artifacts, so you can
work through the curriculum without an emulator or a build toolchain.

<!-- SCREENSHOT/GIF SLOT: docs/assets/demo.gif -->
<!-- Add a demo GIF of the task view → submit → live PASS verdict here before submission. -->
<!-- A full stage walkthrough lives in docs/demo.md. -->

## What it does

- **Graders, not self-assessment.** A task is done when its grader passes, not
  when you decide you've got it. Graders report per-check results rather than a
  bare boolean.
- **Live grading console.** For device-backed tasks the runner streams each step
  of the pipeline — AVD restore, `adb install`, Frida injection, mitmproxy
  capture, each check — so a verdict is traceable to what produced it.
- **Signed pass certificates.** Each pass is signed and verifiable at a public
  `/verify` endpoint, binding the verdict to the task, the learner, and a digest
  of the evidence.
- **Prerequisite-ordered curriculum.** Tasks form a dependency graph; a pathway
  engine suggests your next task from mastery, hints used, and time-to-solve.
- **Optional AI mentor (bring your own key).** Point it at an Anthropic or OpenAI
  key — or any OpenAI-compatible gateway — for tiered hints, snippet
  explanations, and post-task reviews. Keys are encrypted at rest and used
  server-side only; the platform is fully functional without one.
- **MASVS/MASTG-mapped.** Each task cites a MASVS v2 control and the relevant
  MASTG technique or test.
- **Training targets only.** Every target app is an intentionally-vulnerable
  artifact authored in this repo. No real malware, no third-party apps.

## Quickstart

### On your own laptop (workshop / solo mode) — no cloud, no login

Everything runs locally, and live Frida/RASP grading uses your machine's own
Android emulator, so no nested-virtualization host is required. Setup and
troubleshooting: [`docs/preflight.md`](docs/preflight.md) and
[`docs/local-mode.md`](docs/local-mode.md).

```bash
git clone <your-fork-url> masdojo && cd masdojo
make doctor        # check your machine has everything (reports what's missing)
make solo          # http://localhost:5173 — no login, straight into the curriculum
```

`make solo` covers Lab 1 (RE/secrets) and Lab 3 (API abuse), neither of which
needs an emulator. For Lab 2 (live Frida/RASP):

```bash
make avd-up        # create a rooted local AVD + a matching frida-server
make avd-check     # confirm it's ready
make runner-host   # grade against your local AVD (attach mode)
```

### Hosted (multi-user)

The grading runner boots an Android emulator and needs a KVM-enabled host
(nested virtualization). The database, Redis, backend, and frontend run anywhere
Docker runs — see [Runner & KVM](#runner--kvm).

```bash
git clone <your-fork-url> masdojo && cd masdojo
make env                      # writes .env with fresh JWT + master-key secrets
make apps                     # build the vulnerable target APKs (Docker, no host SDK)
make up                       # full stack: db, redis, backend, frontend, runner
```

Open <http://localhost:5173>, register a local account, and start at Module 0.

No KVM host (for example on a Mac)? Everything except the emulator runner still
runs:

```bash
make up-core                  # db, redis, backend, frontend — skips the runner
```

You can browse the whole UI and use the AI mentor. To exercise the grading loop
without an emulator, run the runner in dry-run mode: it grades `flag` and
`static_assert` tasks against server-side expected values. For the full emulator
path on a KVM box, see [`docs/deploy-kvm.md`](docs/deploy-kvm.md).

To enable the AI mentor, open Settings → AI Key and save an Anthropic or OpenAI
key. For a custom endpoint (a proxy or OpenAI-compatible gateway), set
`OPENAI_BASE_URL` / `OPENAI_MODEL` (or the `ANTHROPIC_*` equivalents) in `.env`;
see [`.env.example`](.env.example).

## Architecture

```
        ┌────────────┐        ┌──────────────────────────────┐
        │  frontend  │  HTTP  │            backend            │
        │ React + TS │◀──────▶│   FastAPI · auth · pathway    │
        └────────────┘        │   engine · mentor proxy       │
                              └───────┬───────────────┬───────┘
                                      │               │
                              ┌───────▼──────┐  ┌──────▼──────┐
                              │  PostgreSQL  │  │    Redis    │
                              │ users/tasks/ │  │  grading    │
                              │ submissions  │  │  job queue  │
                              └──────────────┘  └──────┬──────┘
                                                       │ consumes jobs
                                              ┌────────▼─────────┐
                                              │      runner      │  KVM host
                                              │ AVD · adb · Frida│
                                              │ mitmproxy· grader│
                                              └──────────────────┘
```

| Component | Stack | Responsibility |
|-----------|-------|----------------|
| `frontend/` | React, TypeScript, Vite, Tailwind | Dashboard skill map, task view, hint panel, live grading, BYOK settings |
| `backend/` | FastAPI, SQLAlchemy, Pydantic, loguru | Auth (JWT), task API, pathway engine, AI mentor proxy, BYOK key management |
| `runner/` | Python worker | Boots/snapshots the AVD, installs the APK, injects Frida, captures with mitmproxy, runs graders |
| `tasks/` | YAML + Python graders | Self-contained curriculum task packages |
| `apps/` | Kotlin | Source for the intentionally-vulnerable training apps |
| `infra/` | Docker | Compose, Dockerfiles, AVD build, seed scripts |
| `docs/` | Markdown | Architecture, authoring guide, MASVS coverage, demo assets |

Design notes: [`docs/architecture.md`](docs/architecture.md).

## Curriculum

Twelve modules (0–11), ordered so each builds the prerequisites for the next,
covering all eight MASVS v2 categories. Full mapping in
[`docs/masvs-coverage.md`](docs/masvs-coverage.md).

| Module | Domain | MASVS focus |
|--------|--------|-------------|
| 0 · Foundations & Tooling | `foundations` | MASVS-CODE (awareness) |
| 1 · Static Analysis & RE | `static-re` | MASVS-STORAGE-1, MASVS-CODE |
| 2 · Local Data Storage | `storage` | MASVS-STORAGE-1/2 |
| 3 · Cryptography | `crypto` | MASVS-CRYPTO-1/2 |
| 4 · Dynamic Instrumentation | `rasp-bypass` | MASVS-RESILIENCE (intro) |
| 5 · Network & Interception | `network` | MASVS-NETWORK-1/2 |
| 6 · SSL Pinning Bypass | `rasp-bypass` | MASVS-NETWORK-2, MASVS-RESILIENCE |
| 7 · Auth & API Abuse | `api-dynamic` | MASVS-AUTH-1/2 |
| 8 · Platform Interaction & IPC | `platform` | MASVS-PLATFORM-1/2/3 |
| 9 · RASP & Anti-Tampering | `rasp-bypass` | MASVS-RESILIENCE-1..4 |
| 10 · Privacy & Data Sharing | `privacy` | MASVS-PRIVACY-1 |
| 11 · Capstone | `capstone` | Cross-MASVS |

All 30 tasks ship a grader that verifies the technique was applied, not just that
a flag matched. Most grade in dry-run from committed artifacts (decoded
resources, prefs/log/backup dumps, real encrypted blobs, captured traffic), so no
emulator or APK build is needed to solve them; the reference tasks (`001`, `005`,
`009`) also run on a live emulator. Module 9 is a tour of RASP techniques — root,
emulator, and debugger detection, anti-Frida, integrity/tamper checks, string
encryption, and a local attestation stub — each with its own bypass. Adding a
comparison grader is usually a one-liner via
[`runner/runner/graders.py`](runner/runner/graders.py); see
[`tasks/_template/`](tasks/_template/) and [`docs/authoring.md`](docs/authoring.md).

## Grading model

Each task declares a `success_type`. The runner returns a
`GradeResult(passed, evidence, checks, score)`:

| `success_type` | What you submit | What the grader asserts |
|----------------|-----------------|-------------------------|
| `flag` | A string | Constant-time match against the expected flag |
| `static_assert` | An extracted value (secret/endpoint) | The value was genuinely present in the target |
| `frida_assert` | A Frida script | A hook fired / a guarded function's return was flipped |
| `network_assert` | A network interaction | A specific endpoint/param/auth-bypass was exercised (via mitmproxy) |

Every job is sandboxed, network-restricted, and hard-timeouted.

## Runner & KVM

The emulator runner needs hardware-accelerated virtualization:

- A Linux host with `/dev/kvm` is the supported path; the runner container is
  launched with `--device /dev/kvm`.
- If KVM isn't available inside containers, run the runner on bare metal against
  the same Redis/Postgres — see
  [`docs/architecture.md`](docs/architecture.md#runner-on-bare-metal).

## Adding a task

Copy [`tasks/_template/`](tasks/_template/) to a new directory under `tasks/`.
The authoring workflow — `task.yaml` schema, grader contract, hint tiers,
building the target app — is in [`docs/authoring.md`](docs/authoring.md).

## License

[Apache-2.0](LICENSE).
