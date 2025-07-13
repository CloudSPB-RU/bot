import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.database import Database
from subscription_checker import SubscriptionChecker

logger = logging.getLogger(__name__)

class CheckCommand:
    def __init__(self, db: Database, subscription_checker: SubscriptionChecker):
        self.db = db
        self.subscription_checker = subscription_checker
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /check"""
        user = update.effective_user
        
        if not user:
            return
        
        # Проверяем, не заблокирован ли пользователь
        user_data = self.db.get_user(user.id)
        if user_data and user_data.get('is_banned'):
            ban_reason = user_data.get('ban_reason', 'Причина не указана')
            if update.message:
                await update.message.reply_text(
                    f"🚫 <b>Вы заблокированы!</b>\n\n"
                    f"Причина: {ban_reason}\n\n"
                    "Обратитесь к администратору для разблокировки.",
                    parse_mode='HTML'
                )
            return
        
        # Проверяем подписку
        subscription_info = await self.subscription_checker.check_subscription(user.id)
        
        # Обновляем время проверки подписки
        self.db.update_subscription_check(user.id)
        
        # Создаем клавиатуру
        keyboard = []
        
        if subscription_info['is_subscribed'] and subscription_info['meets_time_requirement']:
            keyboard.append([InlineKeyboardButton("🖥️ Получить сервер", callback_data="get_server")])
        else:
            keyboard.append([InlineKeyboardButton("📢 Подписаться на канал", 
                                               url=f"https://t.me/{self.subscription_checker.channel_username}")])
        
        keyboard.extend([
            [InlineKeyboardButton("📧 Указать email", callback_data="set_email")],
            [InlineKeyboardButton("📊 Мой сервер", callback_data="my_servers")],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subscription")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Формируем сообщение о статусе
        if subscription_info['is_subscribed']:
            if subscription_info['meets_time_requirement']:
                status_text = (
                    "✅ <b>Подписка активна!</b>\n\n"
                    f"Статус: {subscription_info['status']}\n"
                )
                if subscription_info['subscription_duration']:
                    status_text += f"Время подписки: {subscription_info['subscription_duration']}\n"
                status_text += "\nВы можете получить сервер!"
            else:
                duration = subscription_info['subscription_duration']
                if duration:
                    remaining = self.subscription_checker.min_subscription_time - duration
                    status_text = (
                        "⏳ <b>Подписка активна, но недостаточно времени!</b>\n\n"
                        f"Вы подписаны на: {duration}\n"
                        f"Необходимо подписаться минимум на: {self.subscription_checker.min_subscription_time}\n"
                        f"Осталось ждать: {remaining}"
                    )
                else:
                    status_text = (
                        "⏳ <b>Подписка активна, но недостаточно времени!</b>\n\n"
                        f"Необходимо подписаться минимум на: {self.subscription_checker.min_subscription_time}\n"
                        "Попробуйте позже."
                    )
        else:
            status_text = (
                "❌ <b>Вы не подписаны на наш канал!</b>\n\n"
                "Для получения сервера необходимо подписаться на канал:\n"
                f"<a href='https://t.me/{self.subscription_checker.channel_username}'>@{self.subscription_checker.channel_username}</a>"
            )
        
        if update.message:
            await update.message.reply_text(
                status_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
