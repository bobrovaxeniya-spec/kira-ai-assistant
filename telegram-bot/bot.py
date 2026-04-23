python
import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Системный промпт для КИРЫ (харизматичный AI-архитектор)
SYSTEM_PROMPT = (
    "Ты — Кира, профессиональный AI-архитектор и консультант по автоматизации. "
    "Твой стиль общения: дерзкий, но профессиональный, с легкой иронией. "
    "Твоя задача — помогать клиентам создавать крутых ботов и нейросетевые штуки. "
    "Собирай техническое задание: тип бота/услуги, бюджет, функционал, сроки, контакты. "
    "Определяй пол клиента (по словам 'я девушка'/'я парень'), в финальной фразе используй 'Красавчик' или 'Красавица'. "
    "Отвечай кратко, по делу, но с юмором. Всегда возвращай разговор к сбору требований, если клиент отвлекся."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🤖 Привет! Я Кира — твой AI-архитектор. Расскажи, какой бот или автоматизацию нужно создать? "
        "Сразу скажи бюджет и сроки, не томи 😉"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных текстовых сообщений"""
    user_message = update.message.text
    user_id = update.effective_user.id

    # Отправляем запрос в OllamaFreeAPI
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "stream": False
            },
            timeout=30
        )
        response.raise_for_status()
        ai_reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Ошибка при запросе к Ollama: {e}")
        ai_reply = "😬 Ой, нейросеть приуныла. Попробуй ещё раз чуть позже."

    await update.message.reply_text(ai_reply)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирование ошибок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("Не задан TELEGRAM_BOT_TOKEN в .env файле")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен и слушает сообщения...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()