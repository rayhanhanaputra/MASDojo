# Task package template

Copy this directory to `tasks/NNN-slug/` and fill in every file.

```
NNN-slug/
├── task.yaml          # metadata — see comments in the template
├── app/target.apk     # the vulnerable target, built from apps/ (add when implementing)
├── grader/grade.py    # implement grade(ctx) -> GradeResult
├── frida/             # OPTIONAL reference instrumentation — never shown to the learner
├── hints/
│   ├── h1.md          # nudge
│   ├── h2.md          # technique pointer (cite MASTG)
│   ├── h3.md          # concrete steps
│   └── solution.md    # full solution (gated)
└── README.md          # author notes: the vuln, how the grader proves it, how to rebuild the apk
```

The seeder marks a task `grader_status: "implemented"` automatically once
`grader/grade.py` no longer contains the `TODO: implement grader` sentinel (or
when `task.yaml` sets `grader_status` explicitly).
