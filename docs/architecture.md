# MASDojo Architecture

This document is expanded in milestone 7. It is created early so the README links resolve.

## Components

- **frontend** — React + TypeScript + Vite + Tailwind SPA.
- **backend** — FastAPI service: auth, task API, pathway engine, AI mentor proxy, BYOK key management.
- **runner** — Python worker consuming the Redis grading queue; drives an Android AVD via adb/Frida/mitmproxy.
- **db** — PostgreSQL: users, tasks, submissions, progress, hint usage, encrypted API keys.
- **redis** — grading job queue (and result channel).

## Grading data flow

1. Learner submits a solution in the task view.
2. Backend persists a `submission` row (`status=queued`) and pushes a job onto the Redis grading queue.
3. The runner pops the job, boots/snapshot-restores the AVD, installs the target APK, applies the submission, and runs the task's `grade(ctx)`.
4. The runner writes the `GradeResult` back (submission `status=passed|failed`, evidence, checks, score) and the frontend polls/streams the verdict.

## Runner on bare metal

The emulator needs hardware virtualization. If `/dev/kvm` is not exposable to containers on your host, comment out the `runner` service in `docker-compose.yml` and run the worker directly:

```bash
cd runner
pip install -e .
export REDIS_URL=redis://localhost:6379/0
export DATABASE_URL=postgresql+psycopg://masdojo:masdojo@localhost:5432/masdojo
python -m runner.worker
```

The host must have the Android SDK command-line tools, an AVD named `$AVD_NAME`, `adb`, `frida-tools`, and `mitmproxy` installed. See `infra/README.md`.
