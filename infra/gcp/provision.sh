#!/usr/bin/env bash
# Provision a dedicated GCP project + a nested-virtualization VM for MASDojo's
# Android-emulator grading. Isolated from any existing project.
#
# Prereqs: gcloud installed and `gcloud auth login` done, plus an active billing
# account on the logged-in user.
#
#   infra/gcp/provision.sh            # uses the defaults below
#   PROJECT_ID=masdojo-123 ZONE=... infra/gcp/provision.sh
set -euo pipefail

# ── config (override via env) ─────────────────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-masdojo-dojo-$(date +%s | tail -c 5)}"
PROJECT_NAME="${PROJECT_NAME:-MASDojo}"
REGION="${REGION:-asia-southeast1}"
ZONE="${ZONE:-asia-southeast1-b}"
MACHINE="${MACHINE:-n2-standard-4}"
VM_NAME="${VM_NAME:-masdojo-runner}"
DISK_GB="${DISK_GB:-40}"
IMAGE_FAMILY="${IMAGE_FAMILY:-ubuntu-2204-lts}"
IMAGE_PROJECT="${IMAGE_PROJECT:-ubuntu-os-cloud}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-}"   # auto-detected if empty
SOURCE_CIDR="${SOURCE_CIDR:-0.0.0.0/0}"  # who can reach the app ports

echo "==> project=${PROJECT_ID} zone=${ZONE} machine=${MACHINE}"

# ── billing account ───────────────────────────────────────────────────────────
if [[ -z "${BILLING_ACCOUNT}" ]]; then
  BILLING_ACCOUNT="$(gcloud beta billing accounts list \
    --filter="open=true" --format="value(name)" | head -n1 || true)"
fi
if [[ -z "${BILLING_ACCOUNT}" ]]; then
  echo "!! no open billing account found. Create/enable one, then set BILLING_ACCOUNT." >&2
  exit 1
fi
echo "==> billing account: ${BILLING_ACCOUNT}"

# ── project ───────────────────────────────────────────────────────────────────
if ! gcloud projects describe "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud projects create "${PROJECT_ID}" --name="${PROJECT_NAME}"
fi
gcloud beta billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}"
gcloud config set project "${PROJECT_ID}"

# ── APIs ──────────────────────────────────────────────────────────────────────
gcloud services enable compute.googleapis.com --project="${PROJECT_ID}"

# ── firewall: SSH + the app ports ─────────────────────────────────────────────
gcloud compute firewall-rules create masdojo-allow-app \
  --project="${PROJECT_ID}" \
  --direction=INGRESS --action=ALLOW \
  --rules=tcp:22,tcp:5173,tcp:8000 \
  --source-ranges="${SOURCE_CIDR}" \
  --target-tags=masdojo 2>/dev/null || echo "   (firewall rule already exists)"

# ── VM with nested virtualization ─────────────────────────────────────────────
# --enable-nested-virtualization adds the vmx license so /dev/kvm appears in the
# guest. N2 (Haswell+) supports it; E2 does not.
gcloud compute instances create "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE}" \
  --enable-nested-virtualization \
  --image-family="${IMAGE_FAMILY}" \
  --image-project="${IMAGE_PROJECT}" \
  --boot-disk-size="${DISK_GB}GB" \
  --boot-disk-type=pd-ssd \
  --tags=masdojo

EXTERNAL_IP="$(gcloud compute instances describe "${VM_NAME}" \
  --project="${PROJECT_ID}" --zone="${ZONE}" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"

cat <<EOF

==> VM up.
    project:     ${PROJECT_ID}
    instance:    ${VM_NAME} (${MACHINE}, ${ZONE})
    external IP: ${EXTERNAL_IP}

Next:
  gcloud compute ssh ${VM_NAME} --project=${PROJECT_ID} --zone=${ZONE}
  # then on the VM, verify KVM:  ls -l /dev/kvm
EOF
