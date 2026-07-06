**Full solution.**

`adb backup -f b.ab org.masdojo.notes`, convert with `abe`/`dd`+`tar`, then read `db/notes.txt`: `note#2: recovery phrase -> rec_…`. Submit that `rec_…` value. It is uniquely seeded to you — no shared flag.
