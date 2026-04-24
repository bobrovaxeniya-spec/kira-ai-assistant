# Remote server quick-start (Ubuntu)

This folder contains helper scripts to bootstrap a remote Ubuntu server for
running the kira-ai-assistant via Docker Compose.

Files:
- `remote_setup.sh` — convenience script to install Docker, create user `aiagent`, clone repository and start services. Inspect before running.
- `polling_bot.py` — small script to run Telegram bot in polling mode (no webhook required).

Quick manual steps (safer than running the shell script blindly):

1) SSH to server as root:

```bash
ssh root@217.12.37.21
# then change root password: passwd
```

2) Create non-root user and add to sudoers (optional):

```bash
adduser aiagent
usermod -aG sudo aiagent
usermod -aG docker aiagent
```

3) Install Docker & Compose (official docs recommended). Or run `remote_setup.sh`.

4) Clone repo and copy .env:

```bash
git clone https://github.com/bobrovaxeniya-spec/kira-ai-assistant.git
cd kira-ai-assistant
cp .env.example .env
# edit .env with real values
```

5) Start all services:

```bash
docker compose up -d
docker compose ps
```

6) Apply migrations (from host or inside api container):

```bash
# inside container
docker compose exec -e SKIP_ENGINE_INIT=1 api /bin/sh -c "alembic upgrade head"
```

7) Run Telegram bot in polling mode (optional):

```bash
# inside api container
python deploy/polling_bot.py
```

Notes & security
- Inspect `remote_setup.sh` before running. It attempts to create user `aiagent` and set sudoers.
- Do not expose Telegram token or GITHUB_TOKEN in public repos. Keep `.env` private.
- For production, replace polling with webhook behind HTTPS and a proper domain + cert.
