#!/usr/bin/env bash
set -euo pipefail

# Minimal remote setup script for Ubuntu-based servers.
# Run as root (or with sudo) on the remote host. This script is opinionated
# and intended as a convenience helper. Inspect before running.

echo "=== Updating system packages ==="
apt update && apt upgrade -y

echo "=== Install prerequisites ==="
apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release

echo "=== Install Docker CE & Compose plugin ==="
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

echo "=== Create non-root user 'aiagent' and add to sudo & docker groups ==="
if ! id -u aiagent >/dev/null 2>&1; then
  adduser --gecos "AI Agent,,," --disabled-password aiagent || true
  echo "aiagent ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/aiagent
fi
usermod -aG docker aiagent || true

echo "=== Enable docker service ==="
systemctl enable docker --now

echo "=== Switch to aiagent home and clone repo if needed ==="
sudo -u aiagent bash -lc '
if [ ! -d "$HOME/kira-ai-assistant" ]; then
  git clone https://github.com/bobrovaxeniya-spec/kira-ai-assistant.git "$HOME/kira-ai-assistant"
fi
cd "$HOME/kira-ai-assistant"
cp .env.example .env 2>/dev/null || true
echo "Repo ready in $HOME/kira-ai-assistant — please edit .env as needed: DATABASE_URL, REDIS_URL, TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_ID, etc."
'

echo "=== Starting services with docker compose ==="
cd /root/kira-ai-assistant 2>/dev/null || cd /home/aiagent/kira-ai-assistant
docker compose pull || true
docker compose up -d

echo "Waiting a few seconds for services to become healthy..."
sleep 8
docker compose ps

echo "=== Apply Alembic migrations inside api container ==="
echo "Note: migration will be executed with SKIP_ENGINE_INIT=1 to avoid import-time engine creation."
if docker compose exec -e SKIP_ENGINE_INIT=1 api /bin/sh -c "alembic upgrade head"; then
  echo "Alembic migrations applied successfully"
else
  echo "Alembic failed. Check logs: docker compose logs api -n 200" >&2
fi

echo "=== Optional: run polling bot inside api container ==="
echo "To run polling bot inside the api container in background:"
echo "docker compose exec -d api /bin/sh -c 'python deploy/polling_bot.py'"

echo "=== Optional: install systemd unit for polling bot ==="
if [ -f deploy/polling_bot.service ]; then
  cp deploy/polling_bot.service /etc/systemd/system/polling_bot.service
  systemctl daemon-reload
  systemctl enable --now polling_bot.service || true
  echo "Installed and started systemd unit: polling_bot.service (may fail if docker compose path differs)"
fi

echo "Remote setup script finished. Edit .env and restart services as needed."
