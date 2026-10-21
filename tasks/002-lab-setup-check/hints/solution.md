**Full solution.** The `setup_check.log` artifact ends with a base64 readiness
token once all checks are green. Decode it:

```bash
echo 'TUFTRE9KT3tsNGJfcjM0ZHl9' | base64 -d   # -> MASDOJO{l4b_r34dy}
```

Submit `MASDOJO{l4b_r34dy}`.
