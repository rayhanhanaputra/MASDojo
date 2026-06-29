#!/usr/bin/env python3
"""Provision a dedicated GCP project + nested-virtualization VM for MASDojo via
the REST API (the gcloud CLI hangs in this environment; raw REST works).

Auth: reads an access token from $GCP_TOKEN or `gcloud auth print-access-token`.
Idempotent-ish: skips creation when a resource already exists.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request

# Required: set BILLING_ACCOUNT=billingAccounts/XXXXXX-XXXXXX-XXXXXX in the env.
# Never hardcode a real billing-account id here — it is account-identifying.
BILLING_ACCOUNT = os.environ.get("BILLING_ACCOUNT", "")
PROJECT_ID = os.environ["PROJECT_ID"]
PROJECT_NAME = os.environ.get("PROJECT_NAME", "MASDojo")
ZONE = os.environ.get("ZONE", "asia-southeast1-b")
MACHINE = os.environ.get("MACHINE", "n2-standard-4")
VM_NAME = os.environ.get("VM_NAME", "masdojo-runner")
DISK_GB = int(os.environ.get("DISK_GB", "40"))
# Required: the operator CIDR allowed to reach SSH + the app ports. No fail-open
# default — opening 22/8000 (the key-holding API) to the whole internet must be
# a deliberate choice. Set SOURCE_CIDR="$(curl -s ifconfig.me)/32" for just you.
SOURCE_CIDR = os.environ.get("SOURCE_CIDR", "")


def token() -> str:
    t = os.environ.get("GCP_TOKEN")
    if t:
        return t.strip()
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


if not BILLING_ACCOUNT:
    raise SystemExit(
        "BILLING_ACCOUNT is required, e.g. "
        "BILLING_ACCOUNT=billingAccounts/XXXXXX-XXXXXX-XXXXXX  (find via "
        "`gcloud billing accounts list` or the Cloud Console)."
    )
if not SOURCE_CIDR:
    raise SystemExit(
        "SOURCE_CIDR is required (who may reach SSH + the app ports). "
        'Set your own IP only: SOURCE_CIDR="$(curl -s ifconfig.me)/32". '
        "Use 0.0.0.0/0 only if you truly intend a fully public box."
    )

TOKEN = token()


def api(method: str, url: str, body: dict | None = None,
        quiet_codes: tuple[int, ...] = ()) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        payload = e.read().decode()
        if e.code in quiet_codes:
            return {}
        raise RuntimeError(f"{method} {url} -> {e.code}: {payload}") from None


def log(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def poll(url: str, label: str, done_check, timeout=300, interval=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        op = api("GET", url)
        if done_check(op):
            if op.get("error"):
                raise RuntimeError(f"{label} failed: {json.dumps(op['error'])}")
            return op
        time.sleep(interval)
    raise TimeoutError(f"{label} did not finish in {timeout}s")


# ── 1. project ────────────────────────────────────────────────────────────────
existing = api("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{PROJECT_ID}",
               quiet_codes=(403, 404))
if existing.get("projectId"):
    log(f"project {PROJECT_ID} already exists")
else:
    log(f"creating project {PROJECT_ID}")
    op = api("POST", "https://cloudresourcemanager.googleapis.com/v1/projects",
             {"projectId": PROJECT_ID, "name": PROJECT_NAME})
    poll(f"https://cloudresourcemanager.googleapis.com/v1/{op['name']}",
         "project create", lambda o: o.get("done"))

proj = api("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{PROJECT_ID}")
PROJECT_NUMBER = proj["projectNumber"]
log(f"project number {PROJECT_NUMBER}")

# ── 2. billing ────────────────────────────────────────────────────────────────
log(f"linking billing account …{BILLING_ACCOUNT[-7:]}")
api("PUT", f"https://cloudbilling.googleapis.com/v1/projects/{PROJECT_ID}/billingInfo",
    {"billingAccountName": BILLING_ACCOUNT})

# ── 3. enable compute API ─────────────────────────────────────────────────────
log("enabling compute.googleapis.com (this can take a minute)")
op = api("POST",
         f"https://serviceusage.googleapis.com/v1/projects/{PROJECT_ID}/services/compute.googleapis.com:enable",
         {})
if op.get("name") and not op.get("done"):
    poll(f"https://serviceusage.googleapis.com/v1/{op['name']}",
         "enable compute", lambda o: o.get("done"), timeout=300)
# Settle for API propagation.
time.sleep(10)

COMPUTE = f"https://compute.googleapis.com/compute/v1/projects/{PROJECT_ID}"


def wait_global_op(op: dict, label: str):
    if op.get("status") == "DONE":
        return
    poll(op["selfLink"], label, lambda o: o.get("status") == "DONE")


def wait_zone_op(op: dict, label: str):
    if op.get("status") == "DONE":
        return
    poll(op["selfLink"], label, lambda o: o.get("status") == "DONE")


# ── 4. default network (enabling compute usually auto-creates it) ──────────────
log("ensuring default network exists")
net = api("GET", f"{COMPUTE}/global/networks/default", quiet_codes=(404,))
for _ in range(18):  # up to ~90s for auto-creation
    net = api("GET", f"{COMPUTE}/global/networks/default", quiet_codes=(404,))
    if net.get("name"):
        break
    time.sleep(5)
if not net.get("name"):
    log("default network missing; creating it")
    op = api("POST", f"{COMPUTE}/global/networks",
             {"name": "default", "autoCreateSubnetworks": True})
    wait_global_op(op, "create default network")
    time.sleep(10)

# ── 5. firewall ───────────────────────────────────────────────────────────────
fw = api("GET", f"{COMPUTE}/global/firewalls/masdojo-allow-app", quiet_codes=(404,))
if fw.get("name"):
    log("firewall masdojo-allow-app already exists")
else:
    log("creating firewall (22, 5173, 8000)")
    op = api("POST", f"{COMPUTE}/global/firewalls", {
        "name": "masdojo-allow-app",
        "network": f"projects/{PROJECT_ID}/global/networks/default",
        "direction": "INGRESS",
        "allowed": [{"IPProtocol": "tcp", "ports": ["22", "5173", "8000"]}],
        "sourceRanges": [SOURCE_CIDR],
        "targetTags": ["masdojo"],
    })
    wait_global_op(op, "create firewall")

# ── 6. instance with nested virtualization ────────────────────────────────────
inst = api("GET", f"{COMPUTE}/zones/{ZONE}/instances/{VM_NAME}", quiet_codes=(404,))
if inst.get("name"):
    log(f"instance {VM_NAME} already exists")
else:
    log(f"creating instance {VM_NAME} ({MACHINE}, nested virt ON)")
    body = {
        "name": VM_NAME,
        "machineType": f"zones/{ZONE}/machineTypes/{MACHINE}",
        "advancedMachineFeatures": {"enableNestedVirtualization": True},
        "disks": [{
            "boot": True,
            "autoDelete": True,
            "initializeParams": {
                "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts",
                "diskSizeGb": DISK_GB,
                "diskType": f"zones/{ZONE}/diskTypes/pd-ssd",
            },
        }],
        "networkInterfaces": [{
            "network": f"projects/{PROJECT_ID}/global/networks/default",
            "accessConfigs": [{"type": "ONE_TO_ONE_NAT", "name": "External NAT"}],
        }],
        "tags": {"items": ["masdojo"]},
    }
    op = api("POST", f"{COMPUTE}/zones/{ZONE}/instances", body)
    wait_zone_op(op, "create instance")

inst = api("GET", f"{COMPUTE}/zones/{ZONE}/instances/{VM_NAME}")
ip = inst["networkInterfaces"][0]["accessConfigs"][0].get("natIP", "(pending)")
log(f"DONE. project={PROJECT_ID} vm={VM_NAME} zone={ZONE} external_ip={ip}")
print(json.dumps({"project_id": PROJECT_ID, "project_number": PROJECT_NUMBER,
                  "vm": VM_NAME, "zone": ZONE, "external_ip": ip}))
