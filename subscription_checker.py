import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

class SubscriptionChecker:
    def __init__(self, bot_token: str, channel_username: str):
        self.bot = Bot(token=bot_token)
        self.channel_username = channel_username.lstrip('@')
        self.min_subscription_time = timedelta(minutes=10)  # Минимум 10 минут подписки
    
    async def check_subscription(self, user_id: int) -> Dict[str, Any]:
        """Проверить подписку пользователя на канал"""
        try:
            # Сначала проверяем доступность канала
            try:
                chat = await self.bot.get_chat(f"@{self.channel_username}")
                logger.info(f"Канал найден: {chat.title} (@{chat.username})")
            except Exception as e:
                logger.error(f"Ошибка доступа к каналу @{self.channel_username}: {e}")
                return {
                    'is_subscribed': False,
                    'subscription_duration': None,
                    'meets_time_requirement': False,
                    'join_date': None,
                    'status': 'channel_error',
                    'error': f"Канал недоступен: {str(e)}"
                }
            
            # Получаем информацию о пользователе в канале
            chat_member = await self.bot.get_chat_member(
                chat_id=f"@{self.channel_username}",
                user_id=user_id
            )
            
            logger.info(f"Проверка подписки для пользователя {user_id}: статус = {chat_member.status}")
            
            # Проверяем статус подписки
            if chat_member.status in ['member', 'administrator', 'creator']:
                # Проверяем время подписки (если доступно)
                join_date = getattr(chat_member, 'joined_date', None)
                if join_date:
                    subscription_duration = datetime.now(join_date.tzinfo) - join_date
                    
                    return {
                        'is_subscribed': True,
                        'subscription_duration': subscription_duration,
                        'meets_time_requirement': subscription_duration >= self.min_subscription_time,
                        'join_date': join_date,
                        'status': chat_member.status
                    }
                else:
                    # Если нет даты присоединения, считаем что подписка есть
                    return {
                        'is_subscribed': True,
                        'subscription_duration': None,
                        'meets_time_requirement': True,
                        'join_date': None,
                        'status': chat_member.status
                    }
            else:
                return {
                    'is_subscribed': False,
                    'subscription_duration': None,
                    'meets_time_requirement': False,
                    'join_date': None,
                    'status': chat_member.status
                }
                
        except TelegramError as e:
            logger.error(f"Ошибка проверки подписки для пользователя {user_id}: {e}")
            logger.error(f"Канал: @{self.channel_username}")
            return {
                'is_subscribed': False,
                'subscription_duration': None,
                'meets_time_requirement': False,
                'join_date': None,
                'status': 'error',
                'error': str(e)
            }
    
    async def get_subscription_message(self, user_id: int) -> str:
        """Получить сообщение о статусе подписки"""
        subscription_info = await self.check_subscription(user_id)
        
        if not subscription_info['is_subscribed']:
            return (
                "❌ <b>Вы не подписаны на наш канал!</b>\n\n"
                "Для получения сервера необходимо подписаться на канал:\n"
                f"<a href='https://t.me/{self.channel_username}'>@{self.channel_username}</a>\n\n"
                "После подписки попробуйте снова."
            )
        
        if not subscription_info['meets_time_requirement']:
            duration = subscription_info['subscription_duration']
            if duration:
                remaining = self.min_subscription_time - duration
                minutes_remaining = int(remaining.total_seconds() // 60)
                seconds_remaining = int(remaining.total_seconds() % 60)
                
                return (
                    "⏳ <b>Подписка активна, но недостаточно времени!</b>\n\n"
                    f"Вы подписаны на: {duration}\n"
                    f"Необходимо подписаться минимум на: {self.min_subscription_time}\n"
                    f"Осталось ждать: {minutes_remaining} мин {seconds_remaining} сек\n\n"
                    "Попробуйте позже."
                )
            else:
                return (
                    "⏳ <b>Подписка активна, но недостаточно времени!</b>\n\n"
                    "Необходимо подписаться минимум на 10 минут.\n"
                    "Попробуйте позже."
                )
        
        duration_text = ""
        if subscription_info['subscription_duration']:
            duration_text = f"Вы подписаны на: {subscription_info['subscription_duration']}\n"
        
        return (
            "✅ <b>Подписка активна!</b>\n\n"
            f"{duration_text}"
            "Можете получить сервер."
        ) 