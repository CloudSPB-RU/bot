#!/usr/bin/env python3
"""
Тестовый скрипт для проверки админских функций
"""

import asyncio
import os
from dotenv import load_dotenv
from db.database import Database
from utils.credentials import CredentialGenerator
from commands.admin import AdminCommands
from pterodactyl_api import PterodactylAPI

# Загружаем переменные окружения
load_dotenv()

async def test_credentials_generator():
    """Тест генератора учетных данных"""
    print("🧪 Тестирование генератора учетных данных...")
    
    # Тестируем генерацию учетных данных
    credentials = CredentialGenerator.generate_credentials(123456789, "TestUser")
    
    print(f"✅ Сгенерированные учетные данные:")
    print(f"Username: {credentials['username']}")
    print(f"Password: {credentials['password']}")
    print(f"Email: {credentials['email']}")
    print(f"Telegram ID: {credentials['telegram_id']}")
    
    # Проверяем хеширование пароля
    hashed = CredentialGenerator.hash_password(credentials['password'])
    print(f"✅ Хеш пароля: {hashed[:20]}...")
    
    # Проверяем верификацию
    is_valid = CredentialGenerator.verify_password(credentials['password'], hashed)
    print(f"✅ Верификация пароля: {is_valid}")
    
    print()

async def test_database_functions():
    """Тест функций базы данных"""
    print("🧪 Тестирование функций базы данных...")
    
    db = Database()
    
    # Создаем тестового пользователя
    user_id = 999999999
    db.create_user(user_id, "testuser", "Test", "User")
    
    # Получаем статистику
    all_users = db.get_all_users()
    banned_users = db.get_banned_users()
    all_servers = db.get_all_servers()
    
    print(f"✅ Всего пользователей: {len(all_users)}")
    print(f"✅ Заблокированных пользователей: {len(banned_users)}")
    print(f"✅ Всего серверов: {len(all_servers)}")
    
    # Тестируем создание сервера с учетными данными
    credentials = CredentialGenerator.generate_credentials(user_id, "TestUser")
    success = db.create_server_with_credentials(user_id, "test_server_123", "Test Server", credentials)
    print(f"✅ Создание сервера с учетными данными: {success}")
    
    # Получаем логи
    logs = db.get_recent_action_logs(5)
    print(f"✅ Последние логи: {len(logs)} записей")
    
    print()

async def test_admin_commands():
    """Тест админских команд"""
    print("🧪 Тестирование админских команд...")
    
    db = Database()
    pterodactyl_api = None  # Не тестируем API в этом скрипте
    
    admin_commands = AdminCommands(db, pterodactyl_api)
    
    # Тестируем статистику
    stats = admin_commands.get_statistics()
    print(f"✅ Статистика получена: {bool(stats)}")
    if stats:
        print(f"  - Всего пользователей: {stats.get('total_users', 0)}")
        print(f"  - Активных пользователей: {stats.get('active_users', 0)}")
        print(f"  - Всего серверов: {stats.get('total_servers', 0)}")
    
    # Тестируем логи
    logs = admin_commands.get_recent_logs(5)
    print(f"✅ Логи получены: {len(logs)} записей")
    
    print()

async def test_pterodactyl_api():
    """Тест Pterodactyl API"""
    print("🧪 Тестирование Pterodactyl API...")
    
    api_url = os.getenv("PTERODACTYL_URL", "https://panel.cloudspb.ru")
    api_token = os.getenv("PTERODACTYL_TOKEN")
    
    if not api_token:
        print("❌ PTERODACTYL_TOKEN не найден, пропускаем тест API")
        return
    
    try:
        api = PterodactylAPI(api_url, api_token)
        
        # Тестируем проверку пользователя
        test_email = "test@example.com"
        user_exists = await api.check_user_exists(test_email)
        print(f"✅ Проверка пользователя {test_email}: {user_exists}")
        
        # Тестируем генерацию учетных данных для API
        credentials = CredentialGenerator.generate_credentials(123456789, "TestUser")
        print(f"✅ Учетные данные для API:")
        print(f"  - Username: {credentials['username']}")
        print(f"  - Email: {credentials['email']}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования API: {e}")
    
    print()

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования админских функций...\n")
    
    await test_credentials_generator()
    await test_database_functions()
    await test_admin_commands()
    await test_pterodactyl_api()
    
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main()) 