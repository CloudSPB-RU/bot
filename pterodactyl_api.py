import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class PterodactylAPI:
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def delete_server(self, server_id: str) -> bool:
        """Удалить сервер"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.api_url}/api/application/servers/{server_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 204:
                        logger.info(f"Сервер {server_id} удален")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка удаления сервера: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Ошибка удаления сервера: {e}")
            return False
    
    async def get_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о сервере"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/application/servers/{server_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка получения информации о сервере: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка получения информации о сервере: {e}")
            return None
    
    async def start_server(self, server_id: str) -> bool:
        """Запустить сервер"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/client/servers/{server_id}/power",
                    headers=self.headers,
                    json={"signal": "start"}
                ) as response:
                    if response.status == 204:
                        logger.info(f"Сервер {server_id} запущен")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка запуска сервера: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Ошибка запуска сервера: {e}")
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Остановить сервер"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/client/servers/{server_id}/power",
                    headers=self.headers,
                    json={"signal": "stop"}
                ) as response:
                    if response.status == 204:
                        logger.info(f"Сервер {server_id} остановлен")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка остановки сервера: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Ошибка остановки сервера: {e}")
            return False
    
    async def create_user(self, email: str, username: str, first_name: str, password: str) -> Optional[Dict[str, Any]]:
        """Создать пользователя в Pterodactyl"""
        try:
            user_data = {
                "email": email,
                "username": username,
                "first_name": first_name,
                "last_name": "TelegramUser",  # Можно оставить фиксированным или передавать как параметр
                "password": password,
                "root_admin": False,
                "language": "ru"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/application/users",
                    headers=self.headers,
                    json=user_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"Пользователь создан: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка создания пользователя: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return None

    async def check_user_exists(self, email: Optional[str] = None, username: Optional[str] = None) -> bool:
        """Проверить существование пользователя по email или username"""
        if not email and not username:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                # Получаем список всех пользователей
                async with session.get(
                    f"{self.api_url}/api/application/users",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        users = await response.json()
                        for user in users.get('data', []):
                            user_attrs = user.get('attributes', {})
                            if email and user_attrs.get('email') == email:
                                return True
                            if username and user_attrs.get('username') == username:
                                return True
                        return False
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка проверки пользователя: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Ошибка проверки пользователя: {e}")
            return False

    async def create_server_with_credentials(self, credentials: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Создать сервер с автоматически сгенерированными учетными данными"""
        try:
            # Проверяем, существует ли пользователь
            user_exists = await self.check_user_exists(
                email=credentials.get('email'),
                username=credentials.get('username')
            )
            
            if user_exists:
                logger.error("Пользователь с таким email или username уже существует в Pterodactyl")
                return None
            
            # Создаем пользователя
            user_result = await self.create_user(
                email=credentials['email'],
                username=credentials['username'],
                first_name=credentials['username'],
                password=credentials['password']
            )
            
            if not user_result:
                logger.error("Не удалось создать пользователя в Pterodactyl")
                return None
            
            # Получаем ID созданного пользователя
            user_id = user_result.get('attributes', {}).get('id')
            if not user_id:
                logger.error("Не удалось получить ID пользователя")
                return None
            
            server_name = f"server_{credentials['username']}"
            
            # Получаем доступные allocation
            available_allocation = await self.get_available_allocation()
            if not available_allocation:
                logger.error("Не найдены доступные allocation")
                return None
            
            # Данные для создания сервера
            server_data = {
                "name": server_name,
                "user": user_id,  # Используем ID созданного пользователя
                "nest": 1,  # ID гнезда (nest)
                "egg": 3,   # ID яйца (egg)
                "docker_image": "ghcr.io/pterodactyl/yolks:java_21",
                "startup": "java -Xms128M -XX:MaxRAMPercentage=95.0 -Dterminal.jline=false -Dterminal.ansi=true -jar {{SERVER_JARFILE}}",
                "environment": {
                    "SERVER_JARFILE": "server.jar",
                    "MINECRAFT_VERSION": "latest",
                    "BUILD_NUMBER": "latest"
                },
                "limits": {
                    "memory": 2048,
                    "swap": 0,
                    "disk": 1000,
                    "io": 500,
                    "cpu": 100
                },
                "feature_limits": {
                    "databases": 0,
                    "backups": 0
                },
                "allocation": {
                    "default": available_allocation
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/application/servers",
                    headers=self.headers,
                    json=server_data
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"Сервер создан с учетными данными: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка создания сервера с учетными данными: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка создания сервера с учетными данными: {e}")
            return None
    
    async def get_available_allocation(self) -> Optional[int]:
        """Получить доступный allocation ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/api/application/nests/1/eggs/3",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        egg_data = await response.json()
                        logger.info(f"Получены данные яйца: {egg_data}")
                        
                        # Получаем allocation из настроек яйца или используем первый доступный
                        allocations = egg_data.get('attributes', {}).get('relationships', {}).get('allocations', {}).get('data', [])
                        
                        if allocations:
                            return allocations[0].get('attributes', {}).get('id')
                        else:
                            # Если нет allocation в яйце, получаем первый доступный
                            async with session.get(
                                f"{self.api_url}/api/application/nodes/1/allocations",
                                headers=self.headers
                            ) as alloc_response:
                                if alloc_response.status == 200:
                                    alloc_data = await alloc_response.json()
                                    available_allocations = [
                                        alloc.get('attributes', {}).get('id')
                                        for alloc in alloc_data.get('data', [])
                                        if not alloc.get('attributes', {}).get('assigned')
                                    ]
                                    
                                    if available_allocations:
                                        return available_allocations[0]
                        
                        logger.error("Не найдены доступные allocation")
                        return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка получения allocation: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Ошибка получения allocation: {e}")
            return None 