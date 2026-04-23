FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Copy requirements first (cache pip install)
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project files
COPY . /app

# Ensure .env is not baked into image (we will pass it at runtime with --env-file)

# Run the bot
CMD ["python", "telegram-bot/bot_clean.py"]
