#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Telegram каналу и Pterodactyl API
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot
from pterodactyl_api import PterodactylAPI

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Тестирование подключения к Telegram"""
    bot_token = os.getenv("BOT_TOKEN")
    channel_username = os.getenv("CHANNEL_USERNAME", "@CloudSPBru")
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден в переменных окружения")
        return False
    
    try:
        bot = Bot(token=bot_token)
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"✅ Бот подключен: @{bot_info.username}")
        
        # Проверяем доступ к каналу
        try:
            chat = await bot.get_chat(f"@{channel_username.lstrip('@')}")
            print(f"✅ Канал доступен: {chat.title} (@{chat.username})")
            
            # Проверяем права бота в канале
            bot_member = await bot.get_chat_member(chat.id, bot_info.id)
            print(f"✅ Права бота в канале: {bot_member.status}")
            
            if bot_member.status not in ['administrator', 'creator']:
                print("⚠️ ВНИМАНИЕ: Бот должен быть администратором канала для проверки подписки!")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка доступа к каналу: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False

async def test_pterodactyl_connection():
    """Тестирование подключения к Pterodactyl API"""
    api_token = os.getenv("PTERODACTYL_TOKEN")
    api_url = os.getenv("PTERODACTYL_URL", "https://panel.cloudspb.ru")
    
    if not api_token:
        print("❌ PTERODACTYL_TOKEN не найден в переменных окружения")
        return False
    
    try:
        api = PterodactylAPI(api_url, api_token)
        
        # Тестируем подключение к API
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/api/application/users",
                headers=api.headers
            ) as response:
                if response.status == 200:
                    print(f"✅ Pterodactyl API доступен: {api_url}")
                    return True
                else:
                    print(f"❌ Ошибка API: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Ошибка подключения к Pterodactyl: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🔍 Тестирование подключений...\n")
    
    # Тестируем Telegram
    print("📱 Тестирование Telegram:")
    telegram_ok = await test_telegram_connection()
    
    print("\n🖥️ Тестирование Pterodactyl:")
    pterodactyl_ok = await test_pterodactyl_connection()
    
    print("\n📊 Результаты:")
    if telegram_ok and pterodactyl_ok:
        print("✅ Все подключения работают!")
        print("🚀 Бот готов к запуску")
    else:
        print("❌ Есть проблемы с подключениями")
        if not telegram_ok:
            print("- Проверьте BOT_TOKEN и права бота в канале")
        if not pterodactyl_ok:
            print("- Проверьте PTERODACTYL_TOKEN и доступность панели")

if __name__ == "__main__":
    asyncio.run(main()) 