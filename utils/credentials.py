import secrets
import string
import hashlib
from typing import Dict, Tuple, Optional

class CredentialGenerator:
    """Генератор безопасных учетных данных"""
    
    @staticmethod
    def generate_username(telegram_id: int, first_name: Optional[str] = None) -> str:
        """Генерирует уникальное имя пользователя"""
        base = first_name.lower() if first_name else f"user{telegram_id}"
        # Убираем спецсимволы и ограничиваем длину
        base = ''.join(c for c in base if c.isalnum())[:10]
        # Добавляем случайный суффикс для уникальности
        suffix = secrets.token_hex(3)
        return f"{base}_{suffix}"
    
    @staticmethod
    def generate_password() -> str:
        """Генерирует безопасный пароль"""
        # Используем буквы, цифры и символы
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(12))
    
    @staticmethod
    def generate_email(username: str) -> str:
        """Генерирует email на основе username"""
        return f"{username}@cloudspb.ru"
    
    @staticmethod
    def generate_credentials(telegram_id: int, first_name: Optional[str] = None) -> Dict[str, str]:
        """Генерирует полный набор учетных данных"""
        username = CredentialGenerator.generate_username(telegram_id, first_name)
        password = CredentialGenerator.generate_password()
        email = CredentialGenerator.generate_email(username)
        
        return {
            'username': username,
            'password': password,
            'email': email,
            'telegram_id': str(telegram_id)
        }
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширует пароль для безопасного хранения"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Проверяет пароль"""
        return CredentialGenerator.hash_password(password) == hashed 