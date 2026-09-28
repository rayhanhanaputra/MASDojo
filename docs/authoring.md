# Authoring MASDojo Tasks

A task is a self-contained directory under `tasks/` that the platform loads at
seed time. This guide walks through adding one.

## Anatomy

```
tasks/NNN-slug/
├── task.yaml          # metadata (schema below)
├── app/target.apk     # the vulnerable target, built from apps/
├── grader/
│   ├── grade.py       # implements grade(ctx) -> GradeResult
│   └── expected.json  # server-side expected values (never sent to the client)
├── backend/server.py  # OPTIONAL mock backend (network_assert tasks)
├── frida/             # OPTIONAL reference instrumentation (never shown to learner)
├── hints/
│   ├── h1.md          # nudge
│   ├── h2.md          # technique pointer (cite MASTG)
│   ├── h3.md          # concrete steps
│   └── solution.md    # full solution (gated by the API)
└── README.md          # author notes
```

Start by copying the template:

```bash
cp -r tasks/_template tasks/123-my-task
```

## `task.yaml` schema

```yaml
id: "123-my-task"            # unique slug, also the directory name
title: "Human-readable title"
module: "2"                  # module label for grouping/ordering
order_index: 1               # order within the module
domain: "storage"            # foundations | static-re | storage | crypto | network |
                             # api-dynamic | platform | rasp-bypass | privacy | capstone
masvs: ["MASVS-STORAGE-1"]   # one or more MASVS v2 controls
mastg_refs: ["MASTG-TECH-…"] # verify against the live MASTG
difficulty: 2                # 1..5
prereqs: ["021-secrets-in-prefs"]  # task ids; forms the DAG
objective: "What the learner must achieve."
success_type: "flag"         # flag | static_assert | frida_assert | network_assert
submission_schema:
  flag: "string"
time_estimate_min: 25
is_reference: false
grader_status: "todo"        # "todo" (scaffold) | "implemented"
# For device-backed tasks:
app_package: "org.masdojo.myapp"
launch_activity: ".MainActivity"
interaction_wait_sec: 15      # network_assert: how long to observe traffic
```

The seeder auto-detects `grader_status`: a `grader/grade.py` still containing the
`TODO: implement grader` sentinel is treated as a scaffold; otherwise it's marked
`implemented`. You can also set `grader_status` explicitly.

## The grader

Implement `grade(ctx) -> GradeResult` against the contract in
`runner/runner/grader_api.py`. The context gives you:

| Field | Use |
|-------|-----|
| `ctx.submission` | the learner's payload (`dict`) |
| `ctx.artifacts.expected()` | server-side expected values from `grader/expected.json` |
| `ctx.artifacts.apk_path` | path to `app/target.apk` |
| `ctx.adb` | run adb commands against the booted AVD |
| `ctx.frida` | spawn/attach + inject Frida scripts |
| `ctx.network` | parsed mitmproxy flows (network_assert) |
| `ctx.log` | structured logger |

Return concrete `Check(name, passed, detail)` entries so the learner sees exactly
what passed or failed. Use `constant_time_equals` for flag/secret comparisons.

### Worked references (read these)

- `tasks/001-find-hardcoded-secret` — `static_assert`
- `tasks/005-intercept-api-call` — `network_assert` (with a bundled mock backend)
- `tasks/009-root-detection-bypass` — `frida_assert`

## The target app

Add the vulnerable app under `apps/<name>/` as a standalone Gradle project (see
`apps/README.md`), wire it into `infra/build-apps.sh`, then build:

```bash
infra/build-apps.sh my-app   # emits tasks/123-my-task/app/target.apk
```

Keep any secret/flag in sync between the app source, `grader/expected.json`, and
`hints/solution.md`.

## Hints

Write four files. Tiers 1–3 escalate from a conceptual nudge to concrete steps;
`solution.md` is the full walkthrough. The API gates `solution.md` until the
learner has used tier 3 or made enough failed attempts. Always ground hints in the
task's MASTG reference.

## Verify

```bash
# Seed and confirm the task loads and its DAG resolves
docker compose up -d db redis backend

# Reference graders are covered by unit tests:
cd runner && pytest tests/test_reference_graders.py
```

Then exercise a real PASS/FAIL round-trip on a KVM host before publishing.
