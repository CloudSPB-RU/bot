#!/usr/bin/env python3
"""
Тестовый скрипт для проверки allocation в Pterodactyl
"""

import asyncio
import os
from dotenv import load_dotenv
from pterodactyl_api import PterodactylAPI

# Загружаем переменные окружения
load_dotenv()

async def test_allocation():
    """Тест получения allocation"""
    print("🧪 Тестирование получения allocation...")
    
    api_url = os.getenv("PTERODACTYL_URL", "https://panel.cloudspb.ru")
    api_token = os.getenv("PTERODACTYL_TOKEN")
    
    if not api_token:
        print("❌ PTERODACTYL_TOKEN не найден")
        return
    
    try:
        api = PterodactylAPI(api_url, api_token)
        
        # Тестируем получение allocation
        allocation_id = await api.get_available_allocation()
        
        if allocation_id:
            print(f"✅ Найден доступный allocation: {allocation_id}")
        else:
            print("❌ Не найдены доступные allocation")
            
        # Тестируем создание сервера с учетными данными
        from utils.credentials import CredentialGenerator
        credentials = CredentialGenerator.generate_credentials(123456789, "TestUser")
        
        print(f"✅ Учетные данные для теста:")
        print(f"  - Username: {credentials['username']}")
        print(f"  - Email: {credentials['email']}")
        
        # Пробуем создать сервер
        server_result = await api.create_server_with_credentials(credentials)
        
        if server_result:
            server_id = server_result.get('attributes', {}).get('identifier')
            server_name = server_result.get('attributes', {}).get('name')
            print(f"✅ Сервер создан успешно!")
            print(f"  - Server ID: {server_id}")
            print(f"  - Server Name: {server_name}")
        else:
            print("❌ Ошибка создания сервера")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

async def main():
    """Основная функция"""
    print("🚀 Тестирование allocation...\n")
    
    await test_allocation()
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main()) 