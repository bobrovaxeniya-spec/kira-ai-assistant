import os
import logging
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import httpx
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


async def async_send_llm_request(user_message: str) -> str:
    """Async version of send_llm_request using httpx.AsyncClient.

    Kept lightweight and with a short timeout to avoid blocking the bot.
    """
    if not OLLAMA_API_URL:
        raise ValueError("OLLAMA_API_URL not set")

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }

    timeout = httpx.Timeout(30.0)
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        resp = await client.post(OLLAMA_API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
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
    aio_app = create_health_app()

    # start stdlib HTTP server in a background thread bound to HEALTH_PORT
    Handler = create_health_app()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    thread = threading.Thread(target=server.serve_forever, name="health-server", daemon=True)
    thread.start()
    application.bot_data["health_server"] = server
    application.bot_data["health_thread"] = thread
    logger.info("Health endpoint started at http://0.0.0.0:%s/health", port)


async def _stop_aiohttp(application: "Application") -> None:
    """Post-shutdown hook: cleanup aiohttp runner if present."""
    server = application.bot_data.pop("health_server", None)
    thread = application.bot_data.pop("health_thread", None)
    if server is not None:
        try:
            server.shutdown()
            server.server_close()
            logger.info("Health endpoint stopped (server shutdown)")
        except Exception as e:
            logger.error("Error shutting down health server: %s", e)
    if thread is not None and thread.is_alive():
        try:
            thread.join(timeout=2)
        except Exception:
            logger.debug("Health thread did not exit cleanly")


def create_health_app():
    """Create a simple stdlib HTTP handler class for health/readiness.

    We return the handler class so tests can instantiate a server around it.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"ok")
                return

            if self.path == "/ready":
                if not OLLAMA_API_URL:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b"OLLAMA_API_URL not configured")
                    return

                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": "ping"}],
                    "stream": False,
                }
                try:
                    resp = requests.post(OLLAMA_API_URL, json=payload, timeout=3)
                    if 200 <= resp.status_code < 300:
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"ok")
                    else:
                        self.send_response(503)
                        self.end_headers()
                        body = resp.text.encode("utf-8", errors="replace")
                        self.wfile.write(bollama_error := b"ollama:" + body)
                except Exception as e:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(str(e).encode("utf-8"))
                return

            # Not found
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            logger.debug("healthserver: %s" % (format % args))

    return Handler


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start"""
    await update.message.reply_text(
        "🤖 Привет! Я Кира — твой AI-архитектор. Расскажи, какой бот или автоматизацию нужно создать? "
        "Сразу скажи бюджет и сроки, не томи 😉"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages"""
    if update.message is None or update.message.text is None:
        logger.debug("Received update without message or text")
        return

    user_message = update.message.text

    try:
        try:
            # Prefer async http client to avoid blocking the bot
            ai_reply = await async_send_llm_request(user_message)
            if not ai_reply:
                raise ValueError("Empty reply from LLM")
        except Exception as e:
            logger.error(f"Ошибка при запросе к Ollama (async): {e}")
            # fallback to sync implementation if async fails for any reason
            try:
                ai_reply = send_llm_request(user_message)
            except Exception as e2:
                logger.error(f"Fallback sync LLM request failed: {e2}")
                ai_reply = "😬 Ой, нейросеть приуныла. Попробуй ещё раз чуть позже."

    except Exception:
        logger.exception("Unhandled error while processing message")
        ai_reply = "😬 Произошла ошибка при обработке вашего запроса. Попробуйте позже."

    await update.message.reply_text(ai_reply)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    # `add_error_handler` expects a callback accepting `object` as the update type
    # Keep runtime behavior: log the exception info from context
    logger.error(msg="Exception while handling an update:", exc_info=getattr(context, "error", None))


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
