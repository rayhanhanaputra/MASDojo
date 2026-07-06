# Engagement briefing — VaultBank capstone

Target: the VaultBank Android app + its live backend at http://localhost:8091.

Your goal: reach the **master vault** (`GET /admin/vault`) and recover the flag
it holds. It is released only to an admin caller — there is no file with the
answer. Put the course together:

- Reconnaissance & RE of the app (Modules 0–1).
- Local storage / crypto to recover cached secrets (Modules 2–3).
- Network interception & pinning bypass to see the API (Modules 5–6).
- Auth abuse against the live API (Module 7): IDOR to enumerate, and — the final
  step — forge an **alg:none** admin token to reach `/admin/vault`.

No walkthrough is provided. Chain what you've learned.
