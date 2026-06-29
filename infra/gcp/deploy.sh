#!/usr/bin/env bash
# Ship MASDojo to the provisioned VM and bring up the full stack (emulator
# grading included). Run from the repo root after infra/gcp/provision.sh.
#
#   PROJECT_ID=masdojo-… ZONE=asia-southeast1-b infra/gcp/deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
ZONE="${ZONE:-asia-southeast1-b}"
VM_NAME="${VM_NAME:-masdojo-runner}"
SSH="gcloud compute ssh ${VM_NAME} --project=${PROJECT_ID} --zone=${ZONE} --command"

echo "==> packaging committed tree (git archive)"
git archive --format=tar.gz -o /tmp/masdojo.tar.gz HEAD

echo "==> copying to VM"
gcloud compute scp /tmp/masdojo.tar.gz \
  "${VM_NAME}:~/masdojo.tar.gz" --project="${PROJECT_ID}" --zone="${ZONE}"

echo "==> installing Docker on the VM (if needed)"
$SSH 'command -v docker >/dev/null 2>&1 || (curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker $USER)'

echo "==> verifying KVM is present"
$SSH 'ls -l /dev/kvm && egrep -c "(vmx|svm)" /proc/cpuinfo'

echo "==> unpacking + building APKs + bringing up the stack"
# sudo -g docker so the freshly-added group membership takes effect this session.
$SSH 'rm -rf ~/masdojo && mkdir -p ~/masdojo && tar -xzf ~/masdojo.tar.gz -C ~/masdojo && \
      cd ~/masdojo && sudo make env && \
      sudo make apps && \
      sudo make up'

echo "==> stack starting. The runner cold-boots the AVD and snapshots it on first run."
echo "    Tail it with:"
echo "      gcloud compute ssh ${VM_NAME} --project=${PROJECT_ID} --zone=${ZONE} --command 'cd ~/masdojo && sudo docker compose logs -f runner'"

IP="$(gcloud compute instances describe "${VM_NAME}" --project="${PROJECT_ID}" --zone="${ZONE}" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
echo ""
echo "==> open the app:  http://${IP}:5173    (API: http://${IP}:8000)"
