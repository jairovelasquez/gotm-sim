# Go-To-Market Live Simulator – VibeFuel (AWS EC2 Monolith)

**Proof-of-concept** monolithic FastAPI app running on **one EC2 instance** in `us-east-1`.

## Stack
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
terraform init
terraform apply -auto-approve

# 3. EC2 will self-bootstrap via user_data.sh -> scripts/bootstrap.sh
```

## Local run (without Bedrock)

Use this when developing locally and you don't want AWS Bedrock dependency.

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
BEDROCK_ENABLED=false PYTHONPATH=. ./venv/bin/python -m scripts.init_db
BEDROCK_ENABLED=false ./venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000`.

## Bedrock notes

- `BEDROCK_ENABLED` defaults to `true`.
- Set `BEDROCK_ENABLED=false` to force deterministic fallback mode.
- In AWS, keep `BEDROCK_ENABLED=true` and ensure IAM + Bedrock model access are enabled.
