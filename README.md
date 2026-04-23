# 🤖 KIRA AI Assistant

Telegram‑бот + лендинг с AI‑консультантом на базе OllamaFreeAPI.

## Возможности
- Отвечает на вопросы клиентов в Telegram
- Собирает техническое задание на создание ботов/автоматизацию
- Имеет харизматичный стиль общения (дерзкий, но профессиональный)
- Сайт‑визитка с чатом (интеграция через Telegram)

## Технологии
- Python + python-telegram-bot
- OllamaFreeAPI (LLM)
- HTML/CSS/JS
- Cloudflare Pages (для сайта)

## Установка и запуск бота локально

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/bobrovaxeniya-spec/kira-ai-assistant.git
   cd kira-ai-assistant
   ```

2. Создайте файл `.env` на основе примера и заполните переменные:
   ```bash
   cp .env.example .env
   # затем откройте .env и подставьте TELEGRAM_BOT_TOKEN и при необходимости OLLAMA_API_URL
   ```

3. Установите зависимости и запустите бота:
   ```bash
   pip install -r requirements.txt
   python telegram-bot/bot.py
   ```

## Контакты и деплой

Сайт собирается как статический сайт в каталоге `website/`. Для деплоя на Cloudflare Pages укажите ветку с контентом и путь `/website` (см. `.github/copilot-instructions.md` для кратких указаний).
# Docker

Для удобного запуска в контейнере добавлены Dockerfile и `docker-compose.yml`.

Советы и быстрые команды:

- Сборка локального образа:

```bash
docker build -t kira-bot:latest .
```

- Запуск контейнера (рекомендуется передавать `.env` через `--env-file`):

```bash
docker run --env-file .env --name kira-bot --restart unless-stopped kira-bot:latest
```

- macOS локальная заметка по Ollama: если Ollama запущен локально на хосте, в `.env` используйте `http://host.docker.internal:11434/v1/chat/completions` в качестве `OLLAMA_API_URL`, иначе контейнер не увидит `localhost` хоста.

- Docker Compose (удобно для dev):

```bash
docker-compose up -d --build
docker-compose logs -f
```

- HEALTHCHECK: в образ добавлена HTTP проверка `curl -f http://127.0.0.1:8080/health` — она опрашивает `/health` на контейнере.

Endpoints:

- GET /health — liveness probe (возвращает 200 OK и тело `ok`).
- GET /ready — readiness probe: быстрый пробный запрос к `OLLAMA_API_URL` (timeout 3s). Возвращает 200 если LLM доступна, иначе 503.

Переменная окружения `HEALTH_PORT` (по умолчанию 8080) управляет портом health-сервера. См. `.env.example`.
# 🤖 KIRA AI Assistant

Telegram‑бот + лендинг с AI‑консультантом на базе OllamaFreeAPI.

## Возможности
- Отвечает на вопросы клиентов в Telegram
- Собирает техническое задание на создание ботов/автоматизацию
- Имеет харизматичный стиль общения (дерзкий, но профессиональный)
- Сайт‑визитка с чатом (интеграция через Telegram)

## Технологии
- Python + python-telegram-bot
- OllamaFreeAPI (LLM)
- HTML/CSS/JS
- Cloudflare Pages (для сайта)

## Установка и запуск бота локально

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/bobrovaxeniya-spec/kira-ai-assistant.git
   cd kira-ai-assistant