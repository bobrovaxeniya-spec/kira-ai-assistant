#!/usr/bin/env python3
"""Simple polling bot runner.

Place this file in the repository and run inside the api container or on any
machine with the repository mounted and environment variables configured.
"""
import os
import sys
import asyncio

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

sys.path.append('/app')  # when run inside container with repo mounted at /app

from app.agents.salesmind import SalesMindAgent


TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN not set in environment')


sessions: dict[str, SalesMindAgent] = {}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = str(update.effective_user.id)
    text = update.message.text
    if user_id not in sessions:
        sessions[user_id] = SalesMindAgent(user_id)
    agent = sessions[user_id]
    reply = await agent.run(text)
    await update.message.reply_text(reply)


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print('Polling bot started')
    app.run_polling()


if __name__ == '__main__':
    main()
