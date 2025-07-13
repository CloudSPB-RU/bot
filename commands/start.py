import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.database import Database
from subscription_checker import SubscriptionChecker
import os

logger = logging.getLogger(__name__)

class StartCommand:
    def __init__(self, db: Database, subscription_checker: SubscriptionChecker):
        self.db = db
        self.subscription_checker = subscription_checker
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        if not user:
            return
        
        # Создаем пользователя в базе данных
        self.db.create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Проверяем подписку
        subscription_message = await self.subscription_checker.get_subscription_message(user.id)
        
        # Создаем клавиатуру
        keyboard = [
            [InlineKeyboardButton("📧 Указать email", callback_data="set_email")],
            [InlineKeyboardButton("🖥️ Получить сервер", callback_data="get_server")],
            [InlineKeyboardButton("📊 Мой сервер", callback_data="my_servers")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 <b>Привет, {user.first_name}!</b>\n\n"
            "Добро пожаловать в бот для получения игровых серверов.\n\n"
            f"{subscription_message}\n\n"
            "Выберите действие:"
        )
        
        if update.message:
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
