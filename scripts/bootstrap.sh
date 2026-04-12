#!/bin/bash
set -euo pipefail

echo "🚀 Starting VibeFuel GTM Simulator Bootstrap..."

# Update system
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
apt-get install -y python3.12 python3.12-venv python3-pip nginx git curl

# Create app directory
mkdir -p /opt/gotm-sim
cd /opt/gotm-sim

# Clone or pull latest code
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    git clone https://github.com/jairovelasquez/gotm-sim.git . || {
        echo "❌ Clone failed. Make sure repo is public."
        exit 1
    }
else
    echo "Pulling latest changes..."
    git pull
fi

# Setup Python virtual environment
python3.12 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Initialize database
echo "Initializing SQLite database..."
venv/bin/python scripts/init_db.py

# Nginx Configuration
echo "Configuring Nginx..."
cp nginx.conf /etc/nginx/sites-available/default
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
rm -f /etc/nginx/sites-enabled/default.old 2>/dev/null || true

# Test and restart Nginx
nginx -t && systemctl restart nginx

# Systemd Service
echo "Installing systemd service..."
cp gotm-sim.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now gotm-sim

# Final status
echo "========================================"
echo "✅ Bootstrap completed!"
echo "App should be available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-hostname)"
echo ""
echo "Run these to check status:"
echo "  sudo systemctl status gotm-sim"
echo "  sudo journalctl -u gotm-sim -f"
echo "========================================"
