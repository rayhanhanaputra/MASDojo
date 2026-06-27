# MASDojo — Mobile App Security Dojo

> A self-hostable, open-source platform for learning **Android application penetration testing** through a guided, adaptive curriculum where every task is graded by a **real Android emulator**.

MASDojo turns the OWASP **MASVS / MASTG** body of knowledge into a hands-on dojo. Each task ships with a deliberately vulnerable target app, a clear objective, and an **automated grader**. When you think you've solved a task, MASDojo boots a real Android AVD, installs the target APK, applies your submission — a recovered secret, a Frida script, or a captured request — runs the grader, and returns a **PASS or FAIL with concrete evidence** of exactly which check passed or failed.

That live, evidence-backed grading loop is the heart of the platform.

<!-- SCREENSHOT/GIF SLOT: docs/assets/demo.gif -->
<!-- Add a demo GIF of the task view → submit → live PASS verdict here before submission. -->
<!-- A full stage walkthrough lives in docs/demo.md. -->

---

## Why MASDojo

- **The emulator is the answer key.** No self-reported "I think I got it." A task is complete only when a real device run verifies your solution.
- **Adaptive pathway.** Tasks form a prerequisite DAG across ten modules. A pathway engine recommends your next task based on mastery, hints used, and time-to-solve.
- **AI mentor, bring-your-own-key.** Plug in your *own* Anthropic or OpenAI API key to unlock Socratic tiered hints, "explain this smali/Frida error," and post-task remediation reviews. Keys are encrypted at rest, used server-side only, and the platform is fully functional without them — so it stays free to host.
- **MASVS-aligned.** Every task maps to a MASVS v2 control and references the relevant MASTG technique/test.
- **Defensive education only.** All target apps are intentionally-vulnerable training artifacts authored in this repo. No real malware, no third-party copyrighted apps.

---

## Quickstart

> **Heads-up:** the grading **runner** boots an Android emulator and therefore needs a **KVM-enabled host** (nested virtualization). The database, Redis, backend, and frontend run anywhere Docker runs. See [Runner & KVM](#runner--kvm).

```bash
git clone <your-fork-url> masdojo && cd masdojo
cp .env.example .env          # then edit secrets (JWT secret, master key)
docker compose up --build     # db, redis, backend, frontend, runner
```

Then open <http://localhost:5173>, register a local account, and start at **Module 0 — Foundations**.

To enable the AI mentor, go to **Settings → AI Key**, paste your Anthropic or OpenAI key, and click **Test & Save**.

---

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
| `frontend/` | React, TypeScript, Vite, Tailwind | Dark terminal-ops UI: dashboard skill map, task view, hint panel, live grading, BYOK settings |
| `backend/` | FastAPI, SQLAlchemy, Pydantic, loguru | Auth (JWT), task API, pathway engine, AI mentor proxy, BYOK key management |
| `runner/` | Python worker | Boots/snapshots AVD, installs APK, injects Frida, captures with mitmproxy, runs graders |
| `tasks/` | YAML + Python graders | Self-contained curriculum task packages |
| `apps/` | Kotlin | Source for the intentionally-vulnerable training apps |
| `infra/` | Docker | Compose, Dockerfiles, AVD build, seed scripts |
| `docs/` | Markdown | Architecture, authoring guide, MASVS coverage, demo assets |

Full design notes: [`docs/architecture.md`](docs/architecture.md).

---

## Curriculum

Ten modules, ordered so each builds the prerequisites for the next. Full mapping in [`docs/masvs-coverage.md`](docs/masvs-coverage.md).

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
| 10 · Capstone | `capstone` | Cross-MASVS |

Three ⭐ **reference tasks** are implemented fully end-to-end (one per dynamic grader type); the rest are scaffolded from [`tasks/_template/`](tasks/_template/) with complete metadata, tiered hints, and a stubbed grader.

---

## Grading model

Each task declares a `success_type`. The runner produces a `GradeResult(passed, evidence, checks, score)`:

| `success_type` | What the learner submits | What the grader asserts |
|----------------|--------------------------|-------------------------|
| `flag` | A string | Constant-time match against the expected flag |
| `static_assert` | An extracted value (secret/endpoint) | The value was genuinely present in the target |
| `frida_assert` | A Frida script | A hook fired / a guarded function's return was flipped |
| `network_assert` | A network interaction | A specific endpoint/param/auth-bypass was exercised (via mitmproxy) |

Every job is sandboxed, network-restricted, and hard-timeouted.

---

## Runner & KVM

The emulator runner requires hardware-accelerated virtualization:

- **Linux host with `/dev/kvm`** is the supported path. The runner container is launched with `--device /dev/kvm`.
- If KVM is unavailable inside containers, run the runner **on bare metal** against the same Redis/Postgres — see [`docs/architecture.md`](docs/architecture.md#runner-on-bare-metal).

---

## Add a task

Drop a new directory under `tasks/` following [`tasks/_template/`](tasks/_template/). The full authoring workflow — `task.yaml` schema, grader contract, hint tiers, building the target app — is in [`docs/authoring.md`](docs/authoring.md).

---

## License

[Apache-2.0](LICENSE).
