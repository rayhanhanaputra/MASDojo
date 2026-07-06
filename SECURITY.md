# Security Policy

MASDojo is a security-training platform. Please read the distinction below before
reporting.

## Intentionally vulnerable by design

The target apps under [`apps/`](apps/), the bundled API under [`vulnapi/`](vulnapi/),
and every challenge in [`tasks/`](tasks/) are **deliberately insecure** — that is
the point of the exercises. Hardcoded secrets, weak crypto, IDOR, missing
pinning, exported components, and similar issues in those directories are **not
vulnerabilities to report** — they are the curriculum. They contain no real data
and target no real backend.

## Reporting a real vulnerability

If you find a genuine security issue in the **platform itself** — the backend
API, the grading runner, authentication, the BYOK key handling, or the
Proof-of-Pwn signing — please report it privately:

- Email: **hanaputrarayhan@gmail.com**
- Do not open a public issue for platform vulnerabilities.
- Include a description, affected component, and reproduction steps.

You'll get an acknowledgement as soon as possible, and a fix will be prioritised.

## Running MASDojo safely

- Run it locally or on a network you control; the target apps and `vulnapi` are
  insecure on purpose.
- The startup guard refuses to boot with placeholder `JWT_SECRET` / `MASTER_KEY`;
  set strong random values (`make env`) for any shared deployment.
- BYOK AI keys are encrypted at rest with your `MASTER_KEY` and never logged.
