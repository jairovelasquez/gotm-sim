#!/bin/bash
set -ex

# Update and install basics
apt-get update -y
apt-get upgrade -y
apt-get install -y python3.12 python3.12-venv python3-pip nginx git curl unzip

# Create app directory
mkdir -p /opt/gotm-sim
cd /opt/gotm-sim

# Clone your repo (CHANGE THIS TO YOUR ACTUAL REPO)
git clone https://github.com/jairovelasquez/gotm-sim.git . || echo "Repo already cloned"

# Run bootstrap
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh

echo "✅ Bootstrap completed successfully"
