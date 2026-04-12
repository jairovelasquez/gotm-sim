#!/bin/bash
set -euxo pipefail

LOG_FILE="/var/log/gotm-bootstrap.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Starting VibeFuel GTM Simulator bootstrap ==="

APP_DIR="/opt/gotm-sim"
APP_USER="ubuntu"
APP_GROUP="www-data"
APP_REPO_URL="${APP_REPO_URL:-https://github.com/jairovelasquez/gotm-sim.git}"
APP_REPO_BRANCH="${APP_REPO_BRANCH:-main}"

export DEBIAN_FRONTEND=noninteractive

echo "--- Updating apt metadata ---"
apt-get update -y

echo "--- Installing system packages ---"
apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  nginx \
  git \
  curl \
  unzip

echo "--- Ensuring app directory exists ---"
mkdir -p "$APP_DIR"
cd "$APP_DIR"

if [ ! -d ".git" ]; then
  echo "--- Cloning repository ---"
  git clone --branch "$APP_REPO_BRANCH" "$APP_REPO_URL" .
else
  echo "--- Repository already exists, updating branch ---"
  git fetch --all
  git checkout "$APP_REPO_BRANCH" || true
  git pull --ff-only origin "$APP_REPO_BRANCH" || true
fi

echo "--- Fixing ownership ---"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

echo "--- Creating virtual environment ---"
python3 -m venv venv

echo "--- Installing Python dependencies ---"
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "--- Verifying required Python modules ---"
./venv/bin/python - <<'PY'
import importlib
mods = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "sqlalchemy",
    "boto3",
]
for mod in mods:
    importlib.import_module(mod)
print("Python dependency check passed")
PY

echo "--- Initializing database ---"
runuser -u "$APP_USER" -- env PYTHONPATH=/opt/gotm-sim ./venv/bin/python -m scripts.init_db

echo "--- Re-applying ownership after build artifacts ---"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

echo "--- Installing systemd service ---"
cp gotm-sim.service /etc/systemd/system/gotm-sim.service
systemctl daemon-reload
systemctl enable gotm-sim

echo "--- Applying nginx config ---"
cp nginx.conf /etc/nginx/sites-available/default
rm -f /etc/nginx/sites-enabled/default.old
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

echo "--- Testing nginx config ---"
nginx -t

echo "--- Restarting services ---"
systemctl restart nginx
systemctl restart gotm-sim

echo "--- Waiting for app to come up ---"
for i in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8000/ >/dev/null; then
    echo "App is responding on 127.0.0.1:8000"
    break
  fi
  echo "App not ready yet ($i/20)"
  sleep 2
done

echo "--- Final service status ---"
systemctl --no-pager --full status gotm-sim || true
systemctl --no-pager --full status nginx || true

echo "=== Bootstrap completed ==="
echo "Log file: $LOG_FILE"
