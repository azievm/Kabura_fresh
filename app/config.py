import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения и перезаписываем их из .env, если нужно
load_dotenv(override=True)

# Токен бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле! Установите переменную окружения BOT_TOKEN.")

# ID администраторов
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]

# Настройки базы данных
# Создаем папку data, если её нет
data_path = Path("data")
data_path.mkdir(exist_ok=True, parents=True)

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///data/bot.db')
# Настройки доставки
DELIVERY_INTERVALS = [
    "9:00 - 12:00",
    "12:00 - 15:00",
    "15:00 - 18:00",
    "18:00 - 21:00"
]

# Минимальный вес для оптовой цены (в кг)
WHOLESALE_MIN_WEIGHT = float(os.getenv('WHOLESALE_MIN_WEIGHT', '5.0'))

# Токен платежной системы
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')
PAYMENT_SHOP_ID = os.getenv('PAYMENT_SHOP_ID')
PAYMENT_SECRET_KEY = os.getenv('PAYMENT_SECRET_KEY') or PAYMENT_TOKEN

# Количество товаров на странице
ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '5'))


# ID чата для уведомлений
NOTIFICATION_CHAT_ID = int(os.getenv('NOTIFICATION_CHAT_ID', '-1002579340956'))

# Настройки HTTP API (Mini App)
API_HOST = os.getenv('API_HOST', '0.0.0.0')
API_PORT = int(os.getenv('API_PORT', '8080'))

# Публичный HTTPS-адрес Mini App (туннель на этапе разработки, домен на проде).
# Если не задан — кнопка "Открыть магазин" в боте не показывается.
MINI_APP_URL = os.getenv('MINI_APP_URL', '')

# CORS: разрешённые origin фронтенда (через запятую).
# По умолчанию "*" (удобно для разработки); на проде укажите свой домен,
# например ALLOWED_ORIGINS=https://shop.example.com
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', '*').split(',') if o.strip()]