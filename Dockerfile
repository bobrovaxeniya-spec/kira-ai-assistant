FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Copy requirements first (cache pip install)
COPY requirements.txt /app/requirements.txt

# Install system deps needed for healthchecks (curl) and process utilities (pgrep)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

# Ensure .env is not baked into image (we will pass it at runtime with --env-file)

# Run the bot (uses telegram-bot/bot.py)
CMD ["python", "telegram-bot/bot.py"]

# Healthcheck: check the bot HTTP /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/health || exit 1
