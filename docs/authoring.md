# Authoring MASDojo Tasks

Expanded in milestone 7. Stub created so README links resolve.

A task is a self-contained directory under `tasks/`:

```
tasks/NNN-slug/
├── task.yaml          # metadata (see schema below)
├── app/target.apk     # built from apps/, the vulnerable target
├── grader/grade.py    # implements grade(ctx) -> GradeResult
├── frida/             # optional reference instrumentation (NOT shown to learner)
├── hints/{h1,h2,h3,solution}.md
└── README.md          # author notes
```

Copy `tasks/_template/` to start. Fill out `task.yaml`, write the four hint files, implement the grader against the contract in `runner/runner/grader_api.py`, and verify the correct MASVS v2 control + current MASTG technique/test IDs against the official MASTG.
