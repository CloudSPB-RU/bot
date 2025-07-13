import logging
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.database import Database
from pterodactyl_api import PterodactylAPI
from utils.credentials import CredentialGenerator

logger = logging.getLogger(__name__)

class AdminCommands:
    def __init__(self, db: Database, pterodactyl_api: PterodactylAPI):
        self.db = db
        self.pterodactyl_api = pterodactyl_api
        self.admin_ids = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
    
    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        return user_id in self.admin_ids
    
    async def get_server_info(self, server_id: str) -> str:
        """Получить подробную информацию о сервере"""
        try:
            # Получаем информацию из Pterodactyl
            server_info = await self.pterodactyl_api.get_server_info(server_id)
            if not server_info:
                return "❌ Сервер не найден в панели Pterodactyl"
            
            # Получаем информацию из базы данных
            db_server = self.db.get_server(server_id)
            if not db_server:
                return "❌ Сервер не найден в базе данных"
            
            # Получаем информацию о владельце
            user_data = self.db.get_user(db_server['user_id'])
            owner_info = "👤 <b>Владелец</b>\nИнформация о владельце не найдена"
            
            if user_data:
                owner_info = (
                    "👤 <b>Владелец</b>\n"
                    f"ID: {user_data.get('telegram_id', 'Не указан')}\n"
                    f"Username: @{user_data.get('username', 'Не указан')}\n"
                    f"Имя: {user_data.get('first_name', 'Не указано')}"
                )
            
            # Получаем параметры сервера
            server_limits = server_info.get('attributes', {}).get('limits', {})
            server_params = (
                "⚙️ <b>Параметры сервера</b>\n"
                f"CPU: {server_limits.get('cpu', 'Не указано')}%\n"
                f"RAM: {server_limits.get('memory', 'Не указано')} MB\n"
                f"Диск: {server_limits.get('disk', 'Не указано')} MB"
            )
            
            # Форматируем информацию
            info = (
                f"🖥️ <b>Информация о сервере</b>\n\n"
                f"ID: {server_id}\n"
                f"Название: {db_server.get('server_name', 'Не указано')}\n"
                f"Статус: {db_server.get('status', 'Не указан')}\n"
                f"Создан: {db_server.get('created_at', 'Не указано')}\n\n"
                f"{owner_info}\n\n"
                f"{server_params}"
            )
            return info
        except Exception as e:
            logger.error(f"Ошибка получения информации о сервере: {e}")
            return "❌ Ошибка получения информации о сервере"
    
    async def handle_server_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /serverinfo"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ <b>Использование:</b> /serverinfo &lt;server_id&gt;\n\n"
                "Пример:\n"
                "/serverinfo abc123",
                parse_mode='HTML'
            )
            return
        
        server_id = context.args[0]
        info = await self.get_server_info(server_id)
        await update.message.reply_text(info, parse_mode='HTML')
    
    async def handle_list_servers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /listservers"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        servers = self.db.get_all_servers()
        if not servers:
            await update.message.reply_text("📊 Нет активных серверов")
            return
        
        response = "📊 <b>Список всех серверов:</b>\n\n"
        for server in servers:
            user_data = self.db.get_user(server['user_id'])
            owner_info = "Владелец не найден"
            if user_data:
                username = user_data.get('username', 'Нет username')
                first_name = user_data.get('first_name', 'Без имени')
                owner_info = f"Владелец: {first_name} (@{username})"
            
            response += (
                f"🖥️ <b>Сервер:</b> {server['server_name']}\n"
                f"ID: {server['pterodactyl_id']}\n"
                f"{owner_info}\n"
                f"Статус: {server['status']}\n"
                f"Создан: {server['created_at']}\n\n"
            )
        
        # Разбиваем на части, если сообщение слишком длинное
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(response, parse_mode='HTML')
    
    def get_statistics(self) -> dict:
        """Получить статистику бота"""
        try:
            # Подсчет пользователей
            total_users = len(self.db.get_all_users())
            banned_users = len(self.db.get_banned_users())
            active_users = total_users - banned_users
            
            # Подсчет серверов
            total_servers = len(self.db.get_all_servers())
            active_servers = len(self.db.get_active_servers())
            
            # Статистика за последние 24 часа
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            new_users_today = len(self.db.get_users_created_after(yesterday))
            new_servers_today = len(self.db.get_servers_created_after(yesterday))
            
            return {
                'total_users': total_users,
                'banned_users': banned_users,
                'active_users': active_users,
                'total_servers': total_servers,
                'active_servers': active_servers,
                'new_users_today': new_users_today,
                'new_servers_today': new_servers_today
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def get_recent_logs(self, limit: int = 10) -> list:
        """Получить последние логи действий"""
        try:
            return self.db.get_recent_action_logs(limit)
        except Exception as e:
            logger.error(f"Ошибка получения логов: {e}")
            return []
    
    async def handle_ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Забанить пользователя"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ <b>Использование:</b> /ban &lt;user_id или username&gt; [причина]\n\n"
                "Примеры:\n"
                "/ban 123456789\n"
                "/ban @username\n"
                "/ban 123456789 Спам",
                parse_mode='HTML'
            )
            return
        
        target = context.args[0]
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else None
        
        # Определяем пользователя
        user_data = None
        if target.startswith('@'):
            username = target[1:]
            user_data = self.db.get_user_by_username(username)
        else:
            try:
                user_id = int(target)
                user_data = self.db.get_user(user_id)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        # Баним пользователя
        if self.db.ban_user(user_data['telegram_id'], reason):
            self.db.log_admin_action(
                update.effective_user.id,
                "ban_user",
                user_data['telegram_id'],
                f"Причина: {reason}"
            )
            await update.message.reply_text(
                f"✅ <b>Пользователь заблокирован!</b>\n\n"
                f"ID: {user_data['telegram_id']}\n"
                f"Username: @{user_data['username']}\n"
                f"Имя: {user_data['first_name']}\n"
                f"Причина: {reason or 'Не указана'}",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Ошибка при блокировке пользователя")
    
    async def handle_unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Разбанить пользователя"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ <b>Использование:</b> /unban &lt;user_id или username&gt;\n\n"
                "Примеры:\n"
                "/unban 123456789\n"
                "/unban @username",
                parse_mode='HTML'
            )
            return
        
        target = context.args[0]
        
        # Определяем пользователя
        user_data = None
        if target.startswith('@'):
            username = target[1:]
            user_data = self.db.get_user_by_username(username)
        else:
            try:
                user_id = int(target)
                user_data = self.db.get_user(user_id)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        # Разбаниваем пользователя
        if self.db.unban_user(user_data['telegram_id']):
            self.db.log_admin_action(
                update.effective_user.id,
                "unban_user",
                user_data['telegram_id']
            )
            await update.message.reply_text(
                f"✅ <b>Пользователь разблокирован!</b>\n\n"
                f"ID: {user_data['telegram_id']}\n"
                f"Username: @{user_data['username']}\n"
                f"Имя: {user_data['first_name']}",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text("❌ Ошибка при разблокировке пользователя")
    
    async def handle_give_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Выдать сервер пользователю с автоматической генерацией учетных данных"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ <b>Использование:</b> /giveserver &lt;user_id или username&gt;\n\n"
                "Примеры:\n"
                "/giveserver 123456789\n"
                "/giveserver @username",
                parse_mode='HTML'
            )
            return
        
        target = context.args[0]
        
        # Определяем пользователя
        user_data = None
        if target.startswith('@'):
            username = target[1:]
            user_data = self.db.get_user_by_username(username)
        else:
            try:
                user_id = int(target)
                user_data = self.db.get_user(user_id)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        # Проверяем, есть ли уже сервер у пользователя
        user_servers = self.db.get_user_servers(user_data['telegram_id'])
        if user_servers:
            await update.message.reply_text(
                f"❌ <b>У пользователя уже есть сервер!</b>\n\n"
                f"ID: {user_data['telegram_id']}\n"
                f"Username: @{user_data['username']}\n"
                f"Количество серверов: {len(user_servers)}",
                parse_mode='HTML'
            )
            return
        
        # Генерируем учетные данные
        credentials = CredentialGenerator.generate_credentials(
            user_data['telegram_id'], 
            user_data['first_name']
        )
        
        # Создаем сервер
        server_result = await self.pterodactyl_api.create_server_with_credentials(credentials)
        if server_result:
            server_id = server_result.get('attributes', {}).get('identifier')
            server_name = server_result.get('attributes', {}).get('name')
            
            # Сохраняем в базу данных
            if self.db.create_server_with_credentials(user_data['telegram_id'], server_id, server_name, credentials):
                self.db.log_admin_action(
                    update.effective_user.id,
                    "give_server",
                    user_data['telegram_id'],
                    f"Server ID: {server_id}, Username: {credentials['username']}"
                )
                
                # Отправляем данные пользователю
                try:
                    await update.get_bot().send_message(
                        chat_id=user_data['telegram_id'],
                        text=f"🎉 <b>Вам выдан сервер!</b>\n\n"
                             f"Server ID: {server_id}\n"
                             f"Username: {credentials['username']}\n"
                             f"Password: {credentials['password']}\n"
                             f"Email: {credentials['email']}\n\n"
                             f"Данные для входа в панель управления.",
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки данных пользователю: {e}")
                
                await update.message.reply_text(
                    f"✅ <b>Сервер выдан!</b>\n\n"
                    f"Пользователь: {user_data['first_name']} (@{user_data['username']})\n"
                    f"Server ID: {server_id}\n"
                    f"Username: {credentials['username']}\n"
                    f"Email: {credentials['email']}\n\n"
                    f"Данные отправлены пользователю.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ Ошибка при сохранении сервера в базу данных")
        else:
            await update.message.reply_text("❌ Ошибка при создании сервера в Pterodactyl")
    
    async def handle_delete_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить сервер пользователя"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        if not context.args or len(context.args) < 1:
            await update.message.reply_text(
                "❌ <b>Использование:</b> /deleteserver &lt;user_id или username&gt;\n\n"
                "Примеры:\n"
                "/deleteserver 123456789\n"
                "/deleteserver @username",
                parse_mode='HTML'
            )
            return
        
        target = context.args[0]
        
        # Определяем пользователя
        user_data = None
        if target.startswith('@'):
            username = target[1:]
            user_data = self.db.get_user_by_username(username)
        else:
            try:
                user_id = int(target)
                user_data = self.db.get_user(user_id)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        if not user_data:
            await update.message.reply_text("❌ Пользователь не найден")
            return
        
        # Получаем серверы пользователя
        user_servers = self.db.get_user_servers(user_data['telegram_id'])
        if not user_servers:
            await update.message.reply_text(
                f"❌ <b>У пользователя нет серверов!</b>\n\n"
                f"ID: {user_data['telegram_id']}\n"
                f"Username: @{user_data['username']}",
                parse_mode='HTML'
            )
            return
        
        # Проверяем и удаляем каждый сервер
        status_message = await update.message.reply_text(
            "⏳ <b>Удаление серверов...</b>",
            parse_mode='HTML'
        )
        
        deleted_count = 0
        failed_servers = []
        
        for server in user_servers:
            server_id = server['pterodactyl_id']
            
            # Проверяем существование сервера в Pterodactyl
            server_info = await self.pterodactyl_api.get_server_info(server_id)
            if not server_info:
                logger.warning(f"Сервер {server_id} не найден в Pterodactyl, удаляем из базы")
                if self.db.delete_server(server_id):
                    deleted_count += 1
                continue
            
            # Пытаемся удалить сервер
            if await self.pterodactyl_api.delete_server(server_id):
                if self.db.delete_server(server_id):
                    deleted_count += 1
            else:
                failed_servers.append(server_id)
        
        # Формируем отчет
        report = f"✅ <b>Результат удаления серверов</b>\n\n"
        report += f"Пользователь: {user_data['first_name']} (@{user_data['username']})\n"
        report += f"Успешно удалено: {deleted_count}\n"
        
        if failed_servers:
            report += f"\n❌ <b>Не удалось удалить:</b>\n"
            for server_id in failed_servers:
                report += f"• {server_id}\n"
        
        if deleted_count > 0:
            self.db.log_admin_action(
                update.effective_user.id,
                "delete_server",
                user_data['telegram_id'],
                f"Удалено серверов: {deleted_count}, Ошибок: {len(failed_servers)}"
            )
        
        await status_message.edit_text(report, parse_mode='HTML')
    
    async def handle_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора"""
        if not update or not update.effective_user or not update.message:
            return
            
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Доступ запрещен", parse_mode='HTML')
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
            [InlineKeyboardButton("🖥️ Управление серверами", callback_data="admin_servers")],
            [InlineKeyboardButton("📝 Логи действий", callback_data="admin_logs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 <b>Панель администратора</b>\n\n"
            "Выберите действие:",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
