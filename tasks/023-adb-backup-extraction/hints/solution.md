**Full solution.** The archive is base64(gzip(tar)). Unpack all three layers:
```bash
base64 -d backup.tar.gz.b64 | tar xzf -
cat apps/org.masdojo.notes/db/notes.txt   # note#2: recovery phrase -> rec_...
```
Submit the `rec_…` recovery key. Seeded per learner. (Real flow: `adb backup -f b.ab <pkg>`, then convert with `abe`/`dd`+`tar`.)
