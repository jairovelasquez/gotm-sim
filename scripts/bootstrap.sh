#!/bin/bash
set -euxo pipefail

LOG_FILE="/var/log/gotm-bootstrap.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Starting VibeFuel GTM Simulator bootstrap ==="

APP_DIR="/opt/gotm-sim"
APP_USER="ubuntu"
APP_GROUP="www-data"

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
  git clone https://github.com/jairovelasquez/gotm-sim.git .
else
  echo "--- Repository already exists, pulling latest ---"
  git fetch --all
  git reset --hard origin/main || git pull --ff-only || true
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
PYTHONPATH=/opt/gotm-sim ./venv/bin/python -m scripts.init_db

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
