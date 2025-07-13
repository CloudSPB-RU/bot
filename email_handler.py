import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.database import Database

logger = logging.getLogger(__name__)

class EmailHandler:
    def __init__(self, db: Database):
        self.db = db
    
    async def handle_email_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик сообщений с email"""
        if not update.message or not update.effective_user or not update.message.text:
            return
        
        email = update.message.text.strip().lower()
        user_id = update.effective_user.id
        
        # Проверяем формат email
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ <b>Неверный формат email!</b>\n\n"
                "Пожалуйста, укажите корректный email адрес.\n"
                "Пример: user@example.com",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Проверяем уникальность email
        if not self.db.is_email_unique(email, exclude_telegram_id=user_id):
            # Блокируем пользователя
            ban_reason = f"Попытка использования неуникального email: {email}"
            if self.db.ban_user(user_id, ban_reason):
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    "🚫 <b>Вы заблокированы!</b>\n\n"
                    "Причина: Попытка использования email, который уже зарегистрирован.\n"
                    f"Email: {email}\n\n"
                    "Для разблокировки обратитесь к администратору.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Ошибка!</b>\n\n"
                    "Произошла ошибка при обработке вашего запроса.\n"
                    "Пожалуйста, обратитесь к администратору.",
                    parse_mode='HTML'
                )
            return
        
        # Сохраняем email
        if self.db.update_user_email(user_id, email):
            keyboard = [
                [InlineKeyboardButton("🖥️ Получить сервер", callback_data="get_server")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "✅ <b>Email успешно сохранен!</b>\n\n"
                f"Ваш email: {email}\n\n"
                "Теперь вы можете получить сервер.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ <b>Ошибка сохранения email!</b>\n\n"
                "Пожалуйста, попробуйте позже или обратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    def get_email_status_message(self, user_id: int) -> str:
        """Получить сообщение о статусе email"""
        user_data = self.db.get_user(user_id)
        
        if not user_data:
            return "❌ <b>Пользователь не найден!</b>"
        
        if user_data.get('email'):
            return (
                f"✅ <b>Email указан:</b> {user_data['email']}\n\n"
                "Вы можете получить сервер!"
            )
        else:
            return (
                "📧 <b>Email не указан!</b>\n\n"
                "Для получения сервера необходимо указать email.\n"
                "Отправьте ваш email в следующем сообщении."
            ) 