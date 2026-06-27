# MASDojo Architecture

MASDojo is a self-hostable platform for learning Android app penetration testing.
Its defining idea: **the emulator runner is the solution-checker**. A task is
complete only when a real Android device run verifies the learner's submission and
returns a PASS/FAIL with concrete evidence.

## Components

```
        ┌────────────┐        ┌──────────────────────────────┐
        │  frontend  │  HTTP  │            backend            │
        │ React + TS │◀──────▶│   FastAPI · auth · pathway    │
        │   (Vite)   │  JWT   │   engine · mentor proxy       │
        └────────────┘        └───────┬───────────────┬───────┘
                                      │               │
                              ┌───────▼──────┐  ┌──────▼──────┐
                              │  PostgreSQL  │  │    Redis    │
                              │ users/tasks/ │  │  grading    │
                              │ submissions/ │  │  job queue  │
                              │ progress/keys│  └──────┬──────┘
                              └──────▲───────┘         │ BLPOP jobs
                                     │ writes results  │
                                     └─────────┬───────┘
                                       ┌───────▼─────────┐
                                       │      runner     │  ← KVM host
                                       │ AVD · adb·Frida │
                                       │ mitmproxy·grader│
                                       └─────────────────┘
```

| Component | Stack | Responsibility |
|-----------|-------|----------------|
| **frontend** | React, TypeScript, Vite, Tailwind | SPA: auth, skill map, task view, hint panel, live grading, BYOK settings, stats |
| **backend** | FastAPI, SQLAlchemy, Pydantic, loguru | Auth (JWT), task API, pathway engine, AI mentor proxy, BYOK key management, job enqueue |
| **runner** | Python worker | Boots/snapshots the AVD, installs APKs, injects Frida, captures with mitmproxy, runs graders, writes results |
| **db** | PostgreSQL | users, tasks, submissions, progress, hint usage, encrypted API keys |
| **redis** | Redis | grading job queue |

## Grading data flow

1. The learner submits a solution in the task view (`POST /submissions/{task_id}`).
2. The backend validates the payload shape for the task's `success_type`, writes a
   `submission` row (`status=queued`), bumps the learner's attempt counter, and
   pushes a JSON job onto the Redis grading queue.
3. The runner `BLPOP`s the job, marks the submission `running`, restores the AVD's
   clean snapshot, installs `target.apk`, and runs the task's `grade(ctx)` under a
   **hard wall-clock timeout**.
4. Per `success_type` the runner prepares the device differently:
   - `static_assert` / `flag` — compares the submission against the task's
     server-side expected values (and, when the APK is present, confirms the value
     is genuinely embedded).
   - `frida_assert` — spawns the app with the learner's Frida script injected and
     observes the effect (e.g. an unlock marker in logcat).
   - `network_assert` — starts the bundled mock backend + an mitmproxy recorder,
     proxies the emulator, triggers the app, and parses the captured flows.
5. The runner writes the `GradeResult` back to Postgres (submission status,
   evidence, per-check results, score; and updates `progress` on a pass).
6. The frontend polls `GET /submissions/{id}` until a terminal status and renders
   the verdict with per-check evidence.

Each job is isolated by snapshot restore, network-restricted, and hard-timed-out,
so one job never leaks state into the next.

## The grading contract

A task's `grader/grade.py` implements `grade(ctx) -> GradeResult`. The contract is
defined in `runner/runner/grader_api.py`:

- `GradingContext` exposes `submission`, `package_dir`, `artifacts` (server-side
  expected values), and the device facets `adb`, `frida`, `network`.
- `GradeResult(passed, evidence, checks, score)` where each `Check(name, passed,
  detail)` is surfaced to the learner.

See `tasks/001`, `tasks/005`, and `tasks/009` for fully-worked reference graders,
one per dynamic grader type.

## Pathway engine

Tasks form a prerequisite DAG grouped by domain. The engine computes each task's
state (`locked` / `available` / `passed`) and recommends the next task. Logic lives
behind a `PathwayStrategy` interface; the default `RuleBasedStrategy` respects
prerequisites, ramps difficulty smoothly, and favours weaker domains. An ML
strategy can be dropped in without touching the API.

## AI mentor (BYOK)

The mentor is bring-your-own-key: each user stores their own Anthropic or OpenAI
key. Keys are validated on entry, **encrypted at rest** (Fernet, keyed by the
server `MASTER_KEY`), used only server-side, never returned to the client after
entry, never logged, and deletable. One internal `AIProvider` interface has two
implementations, so adding providers later is trivial. With no key configured, AI
features disable gracefully and the grader still works fully.

## Runner on bare metal

The emulator needs hardware virtualization. If `/dev/kvm` can't be exposed to
containers on your host, comment out the `runner` service in `docker-compose.yml`
and run the worker directly against the same Redis/Postgres:

```bash
cd runner
pip install .
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+psycopg://masdojo:masdojo@localhost:5432/masdojo
python -m runner.worker
```

The host must have the Android SDK command-line tools, an AVD named `$AVD_NAME`,
`adb`, `frida-tools`, and `mitmproxy`. See `infra/README.md` and `infra/avd/`.

For environments with no emulator at all, set `RUNNER_DRY_RUN=true`: the runner
grades `flag`/`static_assert` tasks (which only compare against server-side
expected values) and skips device-backed types.
