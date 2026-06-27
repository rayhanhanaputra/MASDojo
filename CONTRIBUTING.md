# Contributing to MASDojo

Thanks for your interest in improving MASDojo. This project is a defensive-education platform: contributions must keep that focus.

## Ground rules

- **Defensive education only.** All target apps are intentionally-vulnerable training artifacts authored in this repository. Do not contribute real malware, third-party copyrighted apps, or content whose primary purpose is attacking systems you don't own.
- **Every task maps to MASVS/MASTG.** New curriculum content must cite the correct MASVS v2 control and the relevant MASTG technique/test, verified against the current official MASTG.
- **No secrets in commits.** Never commit a real API key, keystore password, or `.env`.

## Getting set up

```bash
cp .env.example .env
docker compose up --build
```

Backend tests:

```bash
cd backend && pip install -e ".[dev]" && pytest
```

Frontend:

```bash
cd frontend && npm install && npm run dev
```

## Adding a task

See [`docs/authoring.md`](docs/authoring.md). In short: copy `tasks/_template/`, fill out `task.yaml`, write the four hint tiers + solution, implement `grader/grade.py`, and (for a new vulnerability) add the Kotlin target under `apps/`.

## Code style

- **Backend:** `ruff` + `black`, type hints, Pydantic for all request/response models, structured logging via `loguru`.
- **Frontend:** ESLint + Prettier, TypeScript strict mode.
- Conventional-commit messages are appreciated.

## Pull requests

1. Branch off `main`.
2. Keep PRs focused; one task or one feature per PR where possible.
3. Include tests for graders and pathway logic.
4. Describe how you verified the change (a real PASS/FAIL round-trip for grader changes).
