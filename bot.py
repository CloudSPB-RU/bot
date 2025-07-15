import os
import logging
import asyncio
from datetime import datetime
from functools import wraps
from typing import Callable, Any, Coroutine, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from dotenv import load_dotenv

# Импортируем наши модули
from db.database import Database
from subscription_checker import SubscriptionChecker
from pterodactyl_api import PterodactylAPI
from commands.start import StartCommand
from commands.check import CheckCommand
from commands.admin import AdminCommands
from email_handler import EmailHandler

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def async_handler(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]:
    """Декоратор для обработки асинхронных функций"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        return await func(update, context)
    return wrapper

class TelegramBot:
    def __init__(self):
        # Получаем токены из переменных окружения
        self.bot_token = os.getenv("BOT_TOKEN")
        self.pterodactyl_token = os.getenv("PTERODACTYL_TOKEN")
        self.pterodactyl_url = os.getenv("PTERODACTYL_URL", "https://panel.cloudspb.ru")
        self.channel_username = os.getenv("CHANNEL_USERNAME", "@CloudSPBru")
        
        if not self.bot_token:
            raise ValueError("BOT_TOKEN не найден в переменных окружения")
        
        # Инициализируем компоненты
        self.db = Database()
        self.subscription_checker = SubscriptionChecker(self.bot_token, self.channel_username)
        
        # Инициализируем Pterodactyl API только если токен есть
        if self.pterodactyl_token:
            self.pterodactyl_api = PterodactylAPI(self.pterodactyl_url, self.pterodactyl_token)
        else:
            self.pterodactyl_api = None
            logger.warning("PTERODACTYL_TOKEN не найден, функции создания серверов недоступны")
        
        # Инициализируем команды
        self.start_command = StartCommand(self.db, self.subscription_checker)
        self.check_command = CheckCommand(self.db, self.subscription_checker)
        self.admin_commands = AdminCommands(self.db, self.pterodactyl_api) if self.pterodactyl_api else None
        self.email_handler = EmailHandler(self.db)
        
        # Создаем приложение
        self.application = Application.builder().token(self.bot_token).build()
        
        # Словарь для защиты от спама
        self.spam_protection = {}
    
    def is_spam(self, user_id: int) -> bool:
        """Проверка на спам - максимум 5 запросов за 5 секунд"""
        current_time = datetime.now()
        
        if user_id not in self.spam_protection:
            self.spam_protection[user_id] = []
        
        # Удаляем старые запросы (старше 5 секунд)
        self.spam_protection[user_id] = [
            req_time for req_time in self.spam_protection[user_id]
            if (current_time - req_time).seconds < 5
        ]
        
        # Добавляем текущий запрос
        self.spam_protection[user_id].append(current_time)
        
        # Проверяем количество запросов за последние 5 секунд
        if len(self.spam_protection[user_id]) > 5:
            return True
        
        return False
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        if not update.effective_user or not update.message:
            return
            
        if self.is_spam(update.effective_user.id):
            await update.message.reply_text("⚠️ Слишком много запросов. Подождите немного.")
            return
        
        await self.start_command.handle(update, context)
    
    async def handle_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /check"""
        if not update.effective_user or not update.message:
            return
            
        if self.is_spam(update.effective_user.id):
            await update.message.reply_text("⚠️ Слишком много запросов. Подождите немного.")
            return
        
        await self.check_command.handle(update, context)
    
    async def handle_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /ban"""
        if self.admin_commands:
            await self.admin_commands.handle_ban(update, context)
    
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /unban"""
        if self.admin_commands:
            await self.admin_commands.handle_unban(update, context)
    
    async def handle_give_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /giveserver"""
        if self.admin_commands:
            await self.admin_commands.handle_give_server(update, context)
    
    async def handle_delete_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /deleteserver"""
        if self.admin_commands:
            await self.admin_commands.handle_delete_server(update, context)
    
    async def handle_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /admin"""
        if self.admin_commands:
            await self.admin_commands.handle_admin_panel(update, context)
    
    async def handle_server_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /serverinfo"""
        if self.admin_commands:
            await self.admin_commands.handle_server_info(update, context)
    
    async def handle_list_servers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /listservers"""
        if self.admin_commands:
            await self.admin_commands.handle_list_servers(update, context)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback запросов"""
        query = update.callback_query
        if not query or not query.from_user:
            return
            
        await query.answer()
        
        if self.is_spam(query.from_user.id):
            await query.edit_message_text("⚠️ Слишком много запросов. Подождите немного.")
            return
        
        if not query.data:
            return
            
        if query.data == "set_email":
            await self.handle_set_email(query)
        elif query.data == "get_server":
            await self.handle_get_server(query)
        elif query.data == "my_servers":
            await self.handle_my_servers(query)
        elif query.data == "help":
            await self.handle_help(query)
        elif query.data == "check_subscription":
            await self.handle_check_subscription(query)
        elif query.data == "back_to_start":
            await self.handle_back_to_start(query)
        elif query.data.startswith("admin_"):
            await self.handle_admin_callback(query)
    
    async def handle_set_email(self, query) -> None:
        """Обработчик установки email"""
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📧 <b>Укажите ваш email:</b>\n\n"
            "Отправьте ваш email в следующем сообщении.\n"
            "Он будет использован для входа в панель управления сервером.\n\n"
            "Пример: user@example.com",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_get_server(self, query) -> None:
        """Обработчик получения сервера"""
        user_id = query.from_user.id
        
        # Проверяем, не заблокирован ли пользователь
        user_data = self.db.get_user(user_id)
        if user_data and user_data.get('is_banned'):
            ban_reason = user_data.get('ban_reason', 'Причина не указана')
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🚫 <b>Вы заблокированы!</b>\n\n"
                f"Причина: {ban_reason}\n\n"
                "Обратитесь к администратору для разблокировки.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        # Проверяем подписку
        subscription_info = await self.subscription_checker.check_subscription(user_id)
        if not subscription_info['is_subscribed'] or not subscription_info['meets_time_requirement']:
            subscription_message = await self.subscription_checker.get_subscription_message(user_id)
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                subscription_message,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        # Проверяем, есть ли уже сервер у пользователя
        user_servers = self.db.get_user_servers(user_id)
        if user_servers:
            keyboard = [
                [InlineKeyboardButton("📊 Мой сервер", callback_data="my_servers")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ <b>У вас уже есть сервер!</b>\n\n"
                f"Количество серверов: {len(user_servers)}\n"
                "Один пользователь может иметь только один сервер.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        # Проверяем, указан ли email
        if not user_data or not user_data.get('email'):
            keyboard = [
                [InlineKeyboardButton("📧 Указать email", callback_data="set_email")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📧 <b>Сначала укажите email!</b>\n\n"
                "Для получения сервера необходимо указать email.\n"
                "Используйте кнопку '📧 Указать email'",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        # Проверяем email на уникальность в Pterodactyl
        if self.pterodactyl_api:
            try:
                exists = await self.pterodactyl_api.check_user_exists(email=user_data.get('email'))
                if exists:
                    keyboard = [
                        [InlineKeyboardButton("📧 Указать другой email", callback_data="set_email")],
                        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "❌ <b>Ошибка: Email уже используется в панели!</b>\n\n"
                        "Код ошибки: EMAIL_EXISTS\n"
                        "Пожалуйста, укажите другой email.",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    return
            except Exception as e:
                logger.error(f"Ошибка проверки email в Pterodactyl: {e}")
                keyboard = [
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ <b>Ошибка при проверке email!</b>\n\n"
                    "Код ошибки: PT_EMAIL_CHECK\n"
                    "Попробуйте позже.",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return
        # Генерируем безопасные учетные данные с попытками
        from utils.credentials import CredentialGenerator
        max_attempts = 3
        server_result = None
        credentials = None
        error_code = None
        error_message = None
        if not self.pterodactyl_api:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ <b>Сервис создания серверов недоступен!</b>\n\nКод ошибки: PT_API_UNAVAILABLE\nОбратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        for attempt in range(max_attempts):
            credentials = CredentialGenerator.generate_credentials(user_id, user_data.get('first_name'))
            # Проверяем уникальность username/email в Pterodactyl
            try:
                exists = await self.pterodactyl_api.check_user_exists(
                    email=credentials['email'],
                    username=credentials['username']
                )
            except Exception as e:
                logger.error(f"Ошибка проверки username/email в Pterodactyl: {e}")
                exists = True
            if exists:
                if attempt == max_attempts - 1:
                    error_code = "PT_USER_EXISTS"
                    error_message = "Не удалось сгенерировать уникальные данные для панели. Попробуйте позже."
                continue
            # Пытаемся создать сервер
            await query.edit_message_text(
                f"⏳ <b>Создаем сервер... (попытка {attempt+1})</b>\n\nПожалуйста, подождите.",
                parse_mode='HTML'
            )
            try:
                server_result = await self.pterodactyl_api.create_server_with_credentials(credentials)
                if server_result:
                    break
                else:
                    error_code = "PT_SERVER_CREATE"
                    error_message = "Ошибка при создании сервера."
            except Exception as e:
                logger.error(f"Ошибка создания сервера: {e}")
                error_code = "PT_SERVER_CREATE_EXCEPTION"
                error_message = f"Ошибка при создании сервера: {e}"
        if not server_result or not credentials:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"❌ <b>Ошибка при создании сервера!</b>\n\nКод ошибки: {error_code or 'UNKNOWN'}\n{error_message or ''}\nОбратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        server_id = server_result.get('attributes', {}).get('identifier') if server_result else None
        server_name = server_result.get('attributes', {}).get('name') if server_result else None
        if not server_id or not server_name:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ <b>Ошибка при получении данных сервера!</b>\n\nКод ошибки: PT_SERVER_ATTRS\nОбратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        # Сохраняем в базу данных с учетными данными
        if self.db.create_server_with_credentials(user_id, server_id, server_name, credentials):
            keyboard = [
                [InlineKeyboardButton("📊 Мой сервер", callback_data="my_servers")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"✅ <b>Сервер создан успешно!</b>\n\n"
                f"Server ID: {server_id}\n"
                f"Username: {credentials['username']}\n"
                f"Password: {credentials['password']}\n"
                f"Email: {credentials['email']}\n\n"
                "Данные для входа в панель управления.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ <b>Ошибка при сохранении сервера!</b>\n\nКод ошибки: DB_SERVER_SAVE\nОбратитесь к администратору.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def handle_my_servers(self, query) -> None:
        """Обработчик просмотра серверов"""
        user_id = query.from_user.id
        user_servers = self.db.get_user_servers(user_id)
        
        if not user_servers:
            keyboard = [
                [InlineKeyboardButton("🖥️ Получить сервер", callback_data="get_server")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📊 <b>У вас нет серверов</b>\n\n"
                "Используйте кнопку '🖥️ Получить сервер' для создания сервера.",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
            return
        
        server_text = "📊 <b>Ваши серверы:</b>\n\n"
        for i, server in enumerate(user_servers, 1):
            server_text += (
                f"<b>Сервер {i}:</b>\n"
                f"ID: {server['pterodactyl_id']}\n"
                f"Название: {server['server_name']}\n"
                f"Username: {server.get('username', 'Не указан')}\n"
                f"Email: {server.get('email', 'Не указан')}\n"
                f"Статус: {server['status']}\n"
                f"Создан: {server['created_at']}\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(server_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_help(self, query) -> None:
        """Обработчик помощи"""
        help_text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "<b>Команды:</b>\n"
            "/start - Главное меню\n"
            "/check - Проверить подписку\n"
            "/help - Эта справка\n\n"
            "<b>Как получить сервер:</b>\n"
            "1. Подпишитесь на наш канал\n"
            "2. Подождите минимум 10 минут\n"
            "3. Укажите ваш email\n"
            "4. Получите сервер\n\n"
            "<b>Поддержка:</b>\n"
            "По всем вопросам обращайтесь к администратору."
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode='HTML')
    
    async def handle_check_subscription(self, query) -> None:
        """Обработчик повторной проверки подписки"""
        user_id = query.from_user.id
        subscription_message = await self.subscription_checker.get_subscription_message(user_id)
        
        keyboard = [
            [InlineKeyboardButton("🖥️ Получить сервер", callback_data="get_server")],
            [InlineKeyboardButton("📧 Указать email", callback_data="set_email")],
            [InlineKeyboardButton("📊 Мои серверы", callback_data="my_servers")],
            [InlineKeyboardButton("🔄 Проверить снова", callback_data="check_subscription")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back_to_start")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            subscription_message,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_back_to_start(self, query) -> None:
        """Обработчик кнопки 'Назад' - возврат в главное меню"""
        user = query.from_user
        
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
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 <b>Главное меню</b>\n\n"
            f"{subscription_message}\n\n"
            "Выберите действие:"
        )
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_admin_callback(self, query) -> None:
        """Обработчик админских callback"""
        if not self.admin_commands or not self.admin_commands.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Доступ запрещен")
            return
        
        if query.data == "admin_stats":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if not self.admin_commands:
                await query.edit_message_text("❌ Админские функции недоступны")
                return
            
            stats = self.admin_commands.get_statistics()
            if stats:
                stats_text = (
                    "📊 <b>Статистика бота</b>\n\n"
                    f"👥 <b>Пользователи:</b>\n"
                    f"• Всего: {stats.get('total_users', 0)}\n"
                    f"• Активных: {stats.get('active_users', 0)}\n"
                    f"• Заблокированных: {stats.get('banned_users', 0)}\n"
                    f"• Новых за 24ч: {stats.get('new_users_today', 0)}\n\n"
                    f"🖥️ <b>Серверы:</b>\n"
                    f"• Всего: {stats.get('total_servers', 0)}\n"
                    f"• Активных: {stats.get('active_servers', 0)}\n"
                    f"• Новых за 24ч: {stats.get('new_servers_today', 0)}"
                )
            else:
                stats_text = "❌ Ошибка получения статистики"
            
            await query.edit_message_text(
                stats_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif query.data == "admin_users":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "👥 <b>Управление пользователями</b>\n\n"
                "Команды:\n"
                "/ban &lt;user_id&gt; [причина] - Забанить пользователя\n"
                "/unban &lt;user_id&gt; - Разбанить пользователя",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif query.data == "admin_servers":
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🖥️ <b>Управление серверами</b>\n\n"
                "Команды:\n"
                "/giveserver &lt;user_id&gt; - Выдать сервер\n"
                "/deleteserver &lt;user_id&gt; - Удалить сервер",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif query.data == "admin_logs":
            if not self.admin_commands:
                await query.edit_message_text("❌ Админские функции недоступны")
                return
            
            logs = self.admin_commands.get_recent_logs(10)
            if logs:
                logs_text = "📝 <b>Последние действия администраторов:</b>\n\n"
                for log in logs:
                    admin_name = log.get('admin_first_name', 'Неизвестно')
                    action = log.get('action_type', 'Неизвестно')
                    details = log.get('details', '')
                    created_at = log.get('created_at', '')
                    
                    logs_text += (
                        f"👤 <b>{admin_name}</b>\n"
                        f"Действие: {action}\n"
                        f"Детали: {details}\n"
                        f"Время: {created_at}\n\n"
                    )
            else:
                logs_text = "📝 <b>Логи действий</b>\n\nНет записей"
            
            keyboard = [
                [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                logs_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        elif query.data == "admin_panel":
            keyboard = [
                [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
                [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
                [InlineKeyboardButton("🖥️ Управление серверами", callback_data="admin_servers")],
                [InlineKeyboardButton("📝 Логи действий", callback_data="admin_logs")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🔧 <b>Панель администратора</b>\n\n"
                "Выберите действие:",
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений (для email)"""
        if not update.message or not update.message.text:
            return
        
        user = update.effective_user
        if not user:
            return
        
        # Проверяем, не заблокирован ли пользователь
        user_data = self.db.get_user(user.id)
        if user_data and user_data.get('is_banned'):
            ban_reason = user_data.get('ban_reason', 'Причина не указана')
            await update.message.reply_text(
                f"🚫 <b>Вы заблокированы!</b>\n\n"
                f"Причина: {ban_reason}\n\n"
                "Обратитесь к администратору для разблокировки.",
                parse_mode='HTML'
            )
            return
        
        # Обрабатываем email
        await self.email_handler.handle_email_message(update, context)
    
    def setup_handlers(self):
        """Настройка обработчиков"""
        # Команды пользователей
        self.application.add_handler(CommandHandler("start", self.handle_start, block=False))
        self.application.add_handler(CommandHandler("check", self.handle_check, block=False))
        self.application.add_handler(CommandHandler("help", self.handle_help, block=False))
        
        # Админские команды
        self.application.add_handler(CommandHandler("ban", self.handle_ban, block=False))
        self.application.add_handler(CommandHandler("unban", self.handle_unban, block=False))
        self.application.add_handler(CommandHandler("giveserver", self.handle_give_server))
        self.application.add_handler(CommandHandler("deleteserver", self.handle_delete_server))
        self.application.add_handler(CommandHandler("admin", self.handle_admin_panel))
        self.application.add_handler(CommandHandler("serverinfo", self.handle_server_info))
        self.application.add_handler(CommandHandler("listservers", self.handle_list_servers))
        
        # Callback обработчики
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Обработчик сообщений для email
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    def run(self):
        """Запуск бота"""
        self.setup_handlers()
        logger.info("Бот запущен")
        self.application.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()