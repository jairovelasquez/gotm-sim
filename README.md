# Go-To-Market Live Simulator – VibeFuel (AWS EC2 Monolith)

**Proof-of-concept** monolithic FastAPI app running on **one EC2 instance** in `us-east-1`.

**Stack**
- Python 3.12 + FastAPI + Jinja2 + Tailwind (CDN)
- SQLite (local EBS)
- Bedrock (Claude 3 Haiku) with graceful fallback
- Nginx + systemd
- Deterministic simulation + SSE live playback

## Quick Deploy (5 minutes)

```bash
# 1. Clone this repo
git clone <your-repo> gotm-sim && cd gotm-sim

# 2. Deploy infrastructure
cd terraform
terraform init && terraform apply -auto-approve

# 3. EC2 will self-bootstrap via user_data.sh → clones repo → runs scripts/bootstrap.sh