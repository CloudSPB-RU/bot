# Telegram Bot для выдачи игровых серверов

Бот для автоматической выдачи игровых серверов через Pterodactyl панель с проверкой подписки на Telegram канал.

## Возможности

### Для пользователей:
- ✅ Проверка подписки на канал (минимум 10 минут)
- ✅ Указание email для входа в панель
- ✅ Автоматическое создание сервера в Pterodactyl
- ✅ Просмотр своих серверов
- ✅ Защита от спама
- ✅ Красивый интерфейс с кнопками

### Для администраторов:
- ✅ Бан/разбан пользователей по ID или username
- ✅ Выдача серверов пользователям
- ✅ Удаление серверов пользователей
- ✅ Логирование всех действий
- ✅ Панель управления с кнопками

## Установка

### 1. Клонирование репозитория
```bash
git clone https://github.com/CloudSPB-RU/bot/
cd bot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
Создайте файл `.env` на основе `env_example.txt`:

```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# Pterodactyl API
PTERODACTYL_TOKEN=your_pterodactyl_token_here
PTERODACTYL_URL=https://your-panel-domain.ru

# Telegram Channel
CHANNEL_USERNAME=@your_channel_username

# Admin IDs (через запятую)
ADMIN_IDS=123456789,987654321
```

### 4. Настройка базы данных
База данных SQLite создается автоматически при первом запуске в папке `db/users.db`.

### 5. Тестирование подключений
```bash
python test_connection.py
```

### 6. Запуск бота
```bash
python bot.py
```

## Настройка Pterodactyl

### 1. Получение API токена
1. Войдите в панель Pterodactyl как администратор
2. Перейдите в Settings → API Credentials
3. Создайте новый API ключ с правами:
   - Server Creation
   - Server Management
   - User Management

### 2. Настройка серверов
В файле `pterodactyl_api.py` настройте параметры серверов:
- `nest` - ID гнезда
- `egg` - ID яйца
- `limits` - лимиты ресурсов
- `environment` - переменные окружения

## Команды бота

### Пользовательские команды:
- `/start` - Главное меню
- `/check` - Проверить подписку
- `/help` - Справка

### Админские команды:
- `/ban <user_id или @username> [причина]` - Забанить пользователя
- `/unban <user_id или @username>` - Разбанить пользователя
- `/giveserver <user_id или @username>` - Выдать сервер (с автоматической генерацией учетных данных)
- `/deleteserver <user_id или @username>` - Удалить сервер
- `/admin` - Панель администратора

### Админская панель включает:
- 📊 **Статистика** - Подробная статистика пользователей и серверов
- 👥 **Управление пользователями** - Бан/разбан пользователей
- 🖥️ **Управление серверами** - Выдача/удаление серверов
- 📝 **Логи действий** - История действий администраторов

## Структура проекта

```
bot/
├── bot.py                 # Основной файл бота
├── requirements.txt       # Зависимости
├── env_example.txt       # Пример переменных окружения
├── README.md             # Документация
├── db/
│   ├── database.py       # Работа с базой данных
│   └── users.db         # База данных SQLite
├── commands/
│   ├── start.py         # Команда /start
│   ├── check.py         # Команда /check
│   └── admin.py         # Админские команды
├── utils/
│   └── credentials.py   # Генератор безопасных учетных данных
├── subscription_checker.py # Проверка подписки
├── pterodactyl_api.py   # API Pterodactyl
└── test_admin_functions.py # Тест админских функций
```

## Безопасность

### Защита от спама:
- Ограничение 3 запроса за 10 секунд
- Проверка подписки на канал
- Логирование всех действий

### Безопасное создание серверов:
- Автоматическая генерация уникальных учетных данных
- Хеширование паролей для безопасного хранения
- Проверка существования пользователей в панели

### Валидация данных:
- Проверка email формата
- Валидация Telegram ID
- Проверка прав администратора

### База данных:
- SQLite с индексами для быстрой работы
- Транзакции для целостности данных
- Логирование всех изменений

## Логирование

Бот ведет подробные логи всех действий:
- Создание/удаление серверов
- Бан/разбан пользователей
- Ошибки API
- Действия администраторов

## Поддержка

При возникновении проблем:
1. Запустите `python test_connection.py` для диагностики
2. Проверьте логи в консоли
3. Убедитесь в правильности токенов
4. Проверьте доступность Pterodactyl API
5. Убедитесь в правах бота в канале (должен быть администратором)
6. См. файл `SETUP_INSTRUCTIONS.md` для подробных инструкций

## Лицензия

MIT License 