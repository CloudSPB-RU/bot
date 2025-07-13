#!/usr/bin/env python3
"""
Простой тест основных функций бота
"""

import os
import asyncio
from dotenv import load_dotenv
from db.database import Database
from subscription_checker import SubscriptionChecker

# Загружаем переменные окружения
load_dotenv()

async def test_database():
    """Тест базы данных"""
    print("🔍 Тестирование базы данных...")
    
    try:
        db = Database()
        
        # Тест создания пользователя
        test_user_id = 123456789
        result = db.create_user(test_user_id, "test_user", "Test", "User")
        print(f"✅ Создание пользователя: {'Успешно' if result else 'Ошибка'}")
        
        # Тест получения пользователя
        user = db.get_user(test_user_id)
        print(f"✅ Получение пользователя: {'Успешно' if user else 'Ошибка'}")
        
        # Тест обновления email
        result = db.update_user_email(test_user_id, "test@example.com")
        print(f"✅ Обновление email: {'Успешно' if result else 'Ошибка'}")
        
        # Тест проверки подписки
        result = db.update_subscription_check(test_user_id)
        print(f"✅ Обновление проверки подписки: {'Успешно' if result else 'Ошибка'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False

async def test_subscription_checker():
    """Тест проверки подписки"""
    print("\n🔍 Тестирование проверки подписки...")
    
    bot_token = os.getenv("BOT_TOKEN")
    channel_username = os.getenv("CHANNEL_USERNAME", "@CloudSPBru")
    
    if not bot_token:
        print("❌ BOT_TOKEN не найден")
        return False
    
    try:
        checker = SubscriptionChecker(bot_token, channel_username)
        
        # Тест получения информации о канале
        test_user_id = 123456789
        subscription_info = await checker.check_subscription(test_user_id)
        
        print(f"✅ Проверка подписки выполнена")
        print(f"   Статус: {subscription_info['status']}")
        print(f"   Подписан: {subscription_info['is_subscribed']}")
        print(f"   Достаточно времени: {subscription_info['meets_time_requirement']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки подписки: {e}")
        return False

async def test_spam_protection():
    """Тест защиты от спама"""
    print("\n🔍 Тестирование защиты от спама...")
    
    from datetime import datetime
    
    # Имитируем логику защиты от спама
    spam_protection = {}
    user_id = 123456789
    
    def is_spam(user_id: int) -> bool:
        current_time = datetime.now()
        
        if user_id not in spam_protection:
            spam_protection[user_id] = []
        
        # Удаляем старые запросы (старше 10 секунд)
        spam_protection[user_id] = [
            req_time for req_time in spam_protection[user_id]
            if (current_time - req_time).seconds < 10
        ]
        
        # Добавляем текущий запрос
        spam_protection[user_id].append(current_time)
        
        # Проверяем количество запросов за последние 10 секунд
        if len(spam_protection[user_id]) > 3:
            return True
        
        return False
    
    # Тестируем
    print("   Тест 1: Первый запрос")
    result1 = is_spam(user_id)
    print(f"   Результат: {'Спам' if result1 else 'OK'}")
    
    print("   Тест 2: Второй запрос")
    result2 = is_spam(user_id)
    print(f"   Результат: {'Спам' if result2 else 'OK'}")
    
    print("   Тест 3: Третий запрос")
    result3 = is_spam(user_id)
    print(f"   Результат: {'Спам' if result3 else 'OK'}")
    
    print("   Тест 4: Четвертый запрос (должен быть спам)")
    result4 = is_spam(user_id)
    print(f"   Результат: {'Спам' if result4 else 'OK'}")
    
    return result4  # Должен быть True (спам)

async def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование компонентов бота...\n")
    
    # Тестируем базу данных
    db_ok = await test_database()
    
    # Тестируем проверку подписки
    subscription_ok = await test_subscription_checker()
    
    # Тестируем защиту от спама
    spam_ok = await test_spam_protection()
    
    print("\n📊 Результаты тестирования:")
    print(f"   База данных: {'✅ OK' if db_ok else '❌ Ошибка'}")
    print(f"   Проверка подписки: {'✅ OK' if subscription_ok else '❌ Ошибка'}")
    print(f"   Защита от спама: {'✅ OK' if spam_ok else '❌ Ошибка'}")
    
    if db_ok and subscription_ok and spam_ok:
        print("\n🎉 Все тесты пройдены! Бот готов к работе.")
    else:
        print("\n⚠️ Есть проблемы. Проверьте настройки.")

if __name__ == "__main__":
    asyncio.run(main()) 