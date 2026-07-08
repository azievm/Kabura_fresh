# Деплой Kabura Fresh (бот + Mini App)

Бот и HTTP-API Mini App работают **в одном процессе** (`python main.py`):
aiogram опрашивает Telegram, а FastAPI/uvicorn поднимается рядом через
`asyncio.gather`. Отдельный веб-сервер для API запускать не нужно —
достаточно опубликовать один порт под HTTPS.

---

## 1. Что нужно на сервере

- Python 3.11+
- Домен с валидным HTTPS-сертификатом (Telegram Mini App работает **только по HTTPS**)
- Обратный прокси (Caddy или nginx) — терминирует TLS и проксирует на локальный порт бота
- Аккаунт YooKassa (боевой `shopId` + секретный ключ)

---

## 2. Переменные окружения (`.env`)

Создайте `.env` в корне проекта:

```env
# --- Telegram ---
BOT_TOKEN=123456:AA...            # токен бота от @BotFather
ADMIN_IDS=111111111,222222222     # id админов через запятую
NOTIFICATION_CHAT_ID=-100...      # чат/канал для уведомлений о заказах

# --- База ---
DATABASE_URL=sqlite+aiosqlite:///data/bot.db

# --- HTTP API / Mini App ---
API_HOST=0.0.0.0
API_PORT=8080
MINI_APP_URL=https://shop.example.com     # публичный HTTPS-адрес Mini App
ALLOWED_ORIGINS=https://shop.example.com  # CORS: домен фронтенда (без "*" на проде!)

# --- YooKassa ---
PAYMENT_SHOP_ID=ваш_shopId
PAYMENT_SECRET_KEY=ваш_секретный_ключ
```

Важно:
- `MINI_APP_URL` — по нему бот показывает кнопку «Открыть магазин». Пусто → кнопки нет.
- `ALLOWED_ORIGINS` — на проде укажите точный домен. Значение по умолчанию `*`
  удобно в разработке, но открывает CORS всем; в бою так оставлять нельзя.
  Несколько доменов — через запятую.

---

## 3. Сборка фронтенда

FastAPI отдаёт собранный Mini App из `frontend/dist`. Если сборки нет —
показывается диагностическая страница-заглушка.

```bash
cd frontend
npm ci
npm run build        # создаёт frontend/dist
cd ..
```

Пересобирайте `frontend/dist` при каждом изменении фронтенда.

---

## 4. Запуск бота

```bash
python -m venv venv
source venv/bin/activate          # Linux
pip install -r requirements.txt

python main.py
```

Бот начнёт опрос Telegram и поднимет API на `API_HOST:API_PORT` (по умолчанию `0.0.0.0:8080`).

### systemd-сервис (рекомендуется для прода)

`/etc/systemd/system/kabura-bot.service`:

```ini
[Unit]
Description=Kabura Fresh bot + Mini App API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/kabura
ExecStart=/opt/kabura/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/kabura/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kabura-bot
sudo systemctl status kabura-bot
journalctl -u kabura-bot -f          # логи
```

---

## 5. HTTPS-прокси

Mini App и вебхук YooKassa должны быть доступны по HTTPS. Прокси терминирует TLS
и передаёт запросы на `127.0.0.1:8080`.

### Caddy (проще всего — сертификат Let's Encrypt автоматически)

`/etc/caddy/Caddyfile`:

```
shop.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

```bash
sudo systemctl reload caddy
```

### nginx (если уже используется)

```nginx
server {
    listen 443 ssl;
    server_name shop.example.com;

    ssl_certificate     /etc/letsencrypt/live/shop.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shop.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Проверка: `https://shop.example.com/api/health` должен вернуть `{"status":"ok"}`.

---

## 6. Подключение Mini App к боту

1. `@BotFather` → `/mybots` → ваш бот → **Bot Settings → Menu Button** →
   укажите URL `https://shop.example.com`.
2. Убедитесь, что `MINI_APP_URL` в `.env` совпадает с этим адресом —
   тогда кнопка «Открыть магазин» появится и внутри диалога с ботом.

---

## 7. Вебхук YooKassa

После оплаты YooKassa шлёт уведомление на наш сервер. Приложение **не доверяет
телу уведомления**, а перепроверяет статус платежа через API YooKassa —
но URL вебхука настроить всё равно нужно.

В личном кабинете YooKassa → **Настройки → Уведомления (webhook)** укажите:

```
https://shop.example.com/api/yookassa/webhook
```

Отметьте события `payment.succeeded` (как минимум).

> Оплата подтверждается и без вебхука — фронтенд вызывает `/api/payment/confirm`
> после возврата из платёжной формы. Вебхук нужен как страховка на случай,
> если пользователь закрыл окно, не дождавшись редиректа.

---

## 8. База данных и бэкапы

SQLite-файл лежит в `data/bot.db`. Он создаётся автоматически при первом запуске.

Бэкап (можно по cron):

```bash
cp data/bot.db "backups/bot-$(date +%F).db"
```

При обновлении кода делайте бэкап **до** запуска новой версии.

---

## 9. Чек-лист перед боем

- [ ] `.env` заполнен боевыми ключами (YooKassa `live`, не тестовые)
- [ ] `ALLOWED_ORIGINS` = точный домен, не `*`
- [ ] `MINI_APP_URL` совпадает с Menu Button в BotFather
- [ ] `frontend/dist` собран (`npm run build`)
- [ ] `https://<домен>/api/health` отвечает `{"status":"ok"}`
- [ ] Вебхук YooKassa указывает на `/api/yookassa/webhook`
- [ ] Настроен systemd (`Restart=always`) и бэкап базы
- [ ] Тестовый заказ проходит целиком: каталог → корзина → оплата → уведомление админу
