import sqlite3
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "db/users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT UNIQUE,  -- Добавляем UNIQUE constraint
                    is_banned BOOLEAN DEFAULT FALSE,
                    ban_reason TEXT,
                    subscription_checked_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица серверов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    pterodactyl_id TEXT UNIQUE,
                    server_name TEXT,
                    status TEXT DEFAULT 'creating',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Таблица логов действий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    target_user_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Индексы для оптимизации
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_servers_user_id ON servers(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status)')
            
            conn.commit()
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE telegram_id = ?
            ''', (telegram_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def create_user(self, telegram_id: int, username: Optional[str] = None, 
                   first_name: Optional[str] = None, last_name: Optional[str] = None) -> bool:
        """Создать нового пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return False
    
    def update_user_email(self, telegram_id: int, email: str) -> bool:
        """Обновить email пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (email, telegram_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка обновления email: {e}")
            return False
    
    def update_subscription_check(self, telegram_id: int) -> bool:
        """Обновить время проверки подписки"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET subscription_checked_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (telegram_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка обновления проверки подписки: {e}")
            return False
    
    def ban_user(self, telegram_id: int, reason: str) -> bool:
        """Заблокировать пользователя
        
        Args:
            telegram_id: Telegram ID пользователя
            reason: Причина блокировки
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET is_banned = TRUE, ban_reason = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE telegram_id = ?
                ''', (reason, telegram_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка блокировки пользователя: {e}")
            return False
    
    def unban_user(self, telegram_id: int) -> bool:
        """Разбанить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET is_banned = FALSE, ban_reason = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                ''', (telegram_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка разбана пользователя: {e}")
            return False
    
    def get_user_servers(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Получить серверы пользователя"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.* FROM servers s
                JOIN users u ON s.user_id = u.id
                WHERE u.telegram_id = ?
            ''', (telegram_id,))
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_server(self, pterodactyl_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о сервере по его ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM servers WHERE pterodactyl_id = ?
            ''', (pterodactyl_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def create_server(self, telegram_id: int, pterodactyl_id: str, server_name: str) -> bool:
        """Создать запись о сервере"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO servers (user_id, pterodactyl_id, server_name)
                    SELECT id, ?, ? FROM users WHERE telegram_id = ?
                ''', (pterodactyl_id, server_name, telegram_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка создания сервера: {e}")
            return False
    
    def delete_server(self, pterodactyl_id: str) -> bool:
        """Удалить сервер"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM servers WHERE pterodactyl_id = ?', (pterodactyl_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка удаления сервера: {e}")
            return False
    
    def log_admin_action(self, admin_id: int, action_type: str, 
                        target_user_id: Optional[int] = None, details: Optional[str] = None) -> bool:
        """Записать действие администратора"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO action_logs (admin_id, action_type, target_user_id, details)
                    VALUES (?, ?, ?, ?)
                ''', (admin_id, action_type, target_user_id, details))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка записи лога: {e}")
            return False
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по username"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM users WHERE username = ?
            ''', (username,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_banned_users(self) -> List[Dict[str, Any]]:
        """Получить заблокированных пользователей"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE is_banned = TRUE')
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_all_servers(self) -> List[Dict[str, Any]]:
        """Получить все серверы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers')
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_active_servers(self) -> List[Dict[str, Any]]:
        """Получить активные серверы"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers WHERE status = "active"')
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_users_created_after(self, date: datetime) -> List[Dict[str, Any]]:
        """Получить пользователей, созданных после указанной даты"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE created_at >= ?', (date,))
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_servers_created_after(self, date: datetime) -> List[Dict[str, Any]]:
        """Получить серверы, созданные после указанной даты"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM servers WHERE created_at >= ?', (date,))
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def get_recent_action_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить последние логи действий"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT al.*, u.username as admin_username, u.first_name as admin_first_name
                FROM action_logs al
                LEFT JOIN users u ON al.admin_id = u.telegram_id
                ORDER BY al.created_at DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
    
    def create_server_with_credentials(self, telegram_id: int, pterodactyl_id: str, 
                                     server_name: str, credentials: Dict[str, str]) -> bool:
        """Создать запись о сервере с учетными данными"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Проверяем существование колонок
                cursor.execute("PRAGMA table_info(servers)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Добавляем колонки, только если их нет
                if 'username' not in columns:
                    cursor.execute('ALTER TABLE servers ADD COLUMN username TEXT')
                if 'password' not in columns:
                    cursor.execute('ALTER TABLE servers ADD COLUMN password TEXT')
                if 'email' not in columns:
                    cursor.execute('ALTER TABLE servers ADD COLUMN email TEXT')
                
                cursor.execute('''
                    INSERT INTO servers (user_id, pterodactyl_id, server_name, username, password, email)
                    SELECT id, ?, ?, ?, ?, ? FROM users WHERE telegram_id = ?
                ''', (pterodactyl_id, server_name, credentials['username'], 
                      credentials['password'], credentials['email'], telegram_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ошибка создания сервера с учетными данными: {e}")
            return False 

    def is_email_unique(self, email: str, exclude_telegram_id: Optional[int] = None) -> bool:
        """Проверить уникальность email
        
        Args:
            email: Email для проверки
            exclude_telegram_id: ID пользователя, которого нужно исключить из проверки (при обновлении)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if exclude_telegram_id:
                    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ? AND telegram_id != ?', 
                                 (email, exclude_telegram_id))
                else:
                    cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
                count = cursor.fetchone()[0]
                return count == 0
        except Exception as e:
            logger.error(f"Ошибка проверки уникальности email: {e}")
            return False 