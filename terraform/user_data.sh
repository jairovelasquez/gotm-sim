#!/bin/bash
set -ex

# Update and install basics
apt-get update -y
apt-get upgrade -y
apt-get install -y python3 python3-venv python3-pip nginx git curl unzip

# Create app directory
mkdir -p /opt/gotm-sim
cd /opt/gotm-sim

# Clone configured repository/branch
git clone --branch "${repo_branch}" "${repo_url}" . || echo "Repo already cloned"

# Run bootstrap
chmod +x scripts/bootstrap.sh
export APP_REPO_URL="${repo_url}"
export APP_REPO_BRANCH="${repo_branch}"
./scripts/bootstrap.sh

echo "✅ Bootstrap completed successfully"
