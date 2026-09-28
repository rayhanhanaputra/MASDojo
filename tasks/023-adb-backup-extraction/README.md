# 023-adb-backup-extraction — adb Backup Extraction

**Grader type:** `flag` · **MASVS:** MASVS-STORAGE-1, MASVS-STORAGE-2 · status: **implemented**

This task is fully implemented and CI-guarded. Its objective, MASVS/MASTG
mapping, difficulty, and prerequisites live in `task.yaml`; the payload-detection
grader that verifies a submission is `grader/grade.py` (success type: `flag`), and
the escalating hints plus full walkthrough are under `hints/`. The challenge is seeded per-learner (see `challenge/generate.py`), so the derived answer can't be shared.

Per the repo's derive-the-answer principle, no learner-visible file (artifact,
hint tier 1–3, or decompiled snippet) contains the answer verbatim — the learner
must apply the technique to recover it. Server-side expected values, when used,
live in `grader/expected.json` and are never shipped to the client.
