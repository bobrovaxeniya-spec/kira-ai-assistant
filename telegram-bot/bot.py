import os
import logging
import threading
import asyncio
from aiohttp import web
import aiohttp

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


# Load env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# System prompt
SYSTEM_PROMPT = (
    "Ты — Кира, профессиональный AI-архитектор и консультант по автоматизации. "
    "Твой стиль общения: дерзкий, но профессиональный, с легкой иронией. "
    "Твоя задача — помогать клиентам создавать крутых ботов и нейросетевые штуки. "
    "Собирай техническое задание: тип бота/услуги, бюджет, функционал, сроки, контакты. "
    "Определяй пол клиента (по словам 'я девушка'/'я парень'), в финальной фразе используй 'Красавчик' или 'Красавица'. "
    "Отвечай кратко, по делу, но с юмором. Всегда возвращай разговор к сбору требований, если клиент отвлекся."
)


def get_requests_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests.Session with retry/backoff for robust LLM calls."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("HEAD", "GET", "OPTIONS", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def send_llm_request(user_message: str) -> str:
    """Send request to OllamaFreeAPI with retries. Returns reply text or raises."""
    if not OLLAMA_API_URL:
        raise ValueError("OLLAMA_API_URL not set")

    session = get_requests_session()
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }

    resp = session.post(OLLAMA_API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Defensive access
    try:
        return data.get("choices", [])[0].get("message", {}).get("content", "")
    except Exception:
        return ""


async def _start_aiohttp(application: "Application") -> None:
    """Post-init hook: start aiohttp health endpoint on the application's loop.

    This runs the HTTP server in the same asyncio event loop as the bot via
    Application.post_init, so lifecycle is managed by the Application.
    """
    port = int(os.getenv("HEALTH_PORT", "8080"))
    aio_app = web.Application()

    async def _health(request):
        return web.Response(text="ok")

    aio_app.router.add_get("/health", _health)

    async def _ready(request):
        """Readiness check: quick call to OLLAMA_API_URL to verify dependency is reachable."""
        if not OLLAMA_API_URL:
            return web.Response(status=503, text="OLLAMA_API_URL not configured")

        # small probe payload
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": "ping"}],
            "stream": False,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(OLLAMA_API_URL, json=payload) as resp:
                    if 200 <= resp.status < 300:
                        return web.Response(status=200, text="ok")
                    text = await resp.text()
                    return web.Response(status=503, text=f"ollama: status={resp.status} body={text}")
        except Exception as e:
            logger.debug("Readiness probe failed: %s", e)
            return web.Response(status=503, text=f"unreachable: {e}")

    aio_app.router.add_get("/ready", _ready)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    # store runner for cleanup
    application.bot_data["health_runner"] = runner
    logger.info("Health endpoint started at http://0.0.0.0:%s/health", port)


async def _stop_aiohttp(application: "Application") -> None:
    """Post-shutdown hook: cleanup aiohttp runner if present."""
    runner = application.bot_data.pop("health_runner", None)
    if runner is not None:
        try:
            await runner.cleanup()
            logger.info("Health endpoint stopped")
        except Exception as e:
            logger.error("Error cleaning up health endpoint: %s", e)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    await update.message.reply_text(
        "🤖 Привет! Я Кира — твой AI-архитектор. Расскажи, какой бот или автоматизацию нужно создать? "
        "Сразу скажи бюджет и сроки, не томи 😉"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages"""
    user_message = update.message.text

    try:
        try:
            ai_reply = send_llm_request(user_message)
            if not ai_reply:
                raise ValueError("Empty reply from LLM")
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama: {e}")
            ai_reply = "😬 Ой, нейросеть приуныла. Попробуй ещё раз чуть позже."

    except Exception as e:
        logger.exception("Unhandled error while processing message")
        ai_reply = "😬 Произошла ошибка при обработке вашего запроса. Попробуйте позже."

    await update.message.reply_text(ai_reply)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в .env файле")

    # Build application and register lifecycle hooks to run the health endpoint
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(_start_aiohttp)
        .post_shutdown(_stop_aiohttp)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен и слушает сообщения...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
