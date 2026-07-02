#!/usr/bin/env python3
"""
Telegram бот для общения с Claude AI
Установка: pip install python-telegram-bot anthropic
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from anthropic import Anthropic

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализируем клиент Claude
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
client = Anthropic()

# Система сообщений для контекста (память бота)
user_conversations = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - приветствие"""
    await update.message.reply_text(
        "👋 Привет! Я Claude AI бот.\n\n"
        "Просто напишите мне любое сообщение, и я помогу вам!\n\n"
        "Команды:\n"
        "/start - начать\n"
        "/clear - очистить историю разговора\n"
        "/help - помощь"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help - справка"""
    help_text = """
🤖 Я Claude AI - ассистент на основе ИИ.

Я могу помочь с:
✅ Анализом товаров
✅ Написанием текстов
✅ Идеями и советами
✅ Программированием
✅ И много с чем еще!

Просто напишите, что вам нужно.

Специальные команды:
/clear - забыть историю чата (начать заново)
/stats - информация о боте
"""
    await update.message.reply_text(help_text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear - очистить историю"""
    user_id = update.effective_user.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await update.message.reply_text("🗑️ История разговора очищена. Начнем заново!")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - информация о боте"""
    user_id = update.effective_user.id
    messages_count = len(user_conversations.get(user_id, []))
    await update.message.reply_text(
        f"📊 Статистика:\n"
        f"Сообщений в истории: {messages_count}\n"
        f"Модель: Claude 3 Sonnet\n"
        f"Статус: ✅ Онлайн"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик сообщений"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Показываем, что бот печатает
    await update.message.chat.send_action("typing")
    
    try:
        # Получаем или создаем историю разговора для этого пользователя
        if user_id not in user_conversations:
            user_conversations[user_id] = []
        
        # Добавляем новое сообщение пользователя в историю
        user_conversations[user_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Получаем ответ от Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system="Ты полезный ассистент. Отвечай на русском языке, если пользователь пишет по-русски. Будь дружелюбным и помогай конкретно.",
            messages=user_conversations[user_id]
        )
        
        # Получаем текст ответа
        assistant_message = response.content[0].text
        
        # Добавляем ответ в историю
        user_conversations[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Отправляем ответ пользователю
        # Если ответ больше 4096 символов (лимит Telegram), разбиваем на части
        if len(assistant_message) > 4096:
            for i in range(0, len(assistant_message), 4096):
                await update.message.reply_text(assistant_message[i:i+4096])
        else:
            await update.message.reply_text(assistant_message)
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            f"😕 Произошла ошибка: {str(e)}\n\n"
            f"Проверьте, что ваш API ключ Claude активен и у вас достаточно средств на счете."
        )


def main():
    """Главная функция запуска бота"""
    # Получаем токены из переменных окружения
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not telegram_token:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        return
    
    if not CLAUDE_API_KEY:
        logger.error("❌ CLAUDE_API_KEY не установлен!")
        return
    
    # Создаем приложение
    application = Application.builder().token(telegram_token).build()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Добавляем обработчик для обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бот
    logger.info("🚀 Бот запущен!")
    application.run_polling()


if __name__ == '__main__':
    main()
