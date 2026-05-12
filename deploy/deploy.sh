#!/usr/bin/env bash
set -euo pipefail

trap 'echo "Deployment failed." >&2' ERR

run_cmd() {
  echo "+ $*" >&2
  "$@"
}

section() {
  echo "" >&2
  echo "==> $*" >&2
}

FRDB_REPO_DIR="${FRDB_REPO_DIR:-/home/frdb/frdb}"
FRDB_BASE_URL="${FRDB_BASE_URL:-https://frdb.qclub.au}"
FRDB_API_URL="${FRDB_API_URL:-${FRDB_BASE_URL}/api/research-data}"

section "Stopping frdb service as invoking user"
if systemctl is-active --quiet frdb; then
  run_cmd sudo systemctl stop frdb
fi

section "Updating repository as frdb user"
run_cmd sudo -u frdb -H bash -lc "cd ${FRDB_REPO_DIR} && git pull --ff-only"

section "Checking service user"
run_cmd id frdb

section "Updating Python dependencies as frdb user"
run_cmd sudo -u frdb -H bash -lc "cd ${FRDB_REPO_DIR} \
  && python3 -m venv .venv \
  && . .venv/bin/activate \
  && pip install --upgrade pip \
  && pip install -r deploy/requirements.txt"

section "Preparing writable upload directory as frdb user"
run_cmd sudo -u frdb -H bash -lc "mkdir -p ${FRDB_REPO_DIR}/uploads"

section "Checking local settings as frdb user"
run_cmd sudo -u frdb -H bash -lc "cd ${FRDB_REPO_DIR} \
  && test -f local_settings.py \
  && .venv/bin/python -c 'from local_settings import MAIL_CONFIG; assert MAIL_CONFIG.username; assert MAIL_CONFIG.password; assert MAIL_CONFIG.sender'"

section "Starting services as invoking user"
run_cmd sudo systemctl start frdb
run_cmd sudo systemctl restart nginx

section "Verifying deployed app"
echo "+ curl -fsSI ${FRDB_BASE_URL}/" >&2
curl -fsSI "${FRDB_BASE_URL}/" >/dev/null

echo "+ curl -fsS ${FRDB_API_URL}" >&2
api_json=$(curl -fsS "${FRDB_API_URL}")

printf '%s' "${api_json}" | python3 -c "import json, sys; payload = json.load(sys.stdin); assert payload.get('rows'), 'API returned no rows'; assert payload.get('filters'), 'API returned no filters'"

echo "Deployment succeeded. FRDB responded at ${FRDB_BASE_URL}/ and ${FRDB_API_URL}." >&2
