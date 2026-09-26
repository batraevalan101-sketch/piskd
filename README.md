# 🎬 AI Video Generation Telegram Bot

Telegram бот для генерации видео с помощью нейросетей.

## Поддерживаемые провайдеры

| Провайдер | Модель | Режимы |
|---|---|---|
| 🌱 SeedDance 2.5 | seedance-1-lite / pro | T2V, I2V |
| ⚡ Kling AI | Kling v2 Omni Flash | T2V, I2V |
| 🌊 Luma Dream Machine | Flow (Dream Machine) | T2V, I2V |
| 🎥 Runway ML | Gen-4 Turbo | T2V, I2V |

---

## Установка

### 1. Клонируй репозиторий

```bash
git clone <your-repo>
cd tg_video_bot
```

### 2. Установи зависимости

```bash
pip install -r requirements.txt
```

### 3. Настрой переменные окружения

```bash
cp .env.example .env
# Открой .env и вставь свои ключи
```

### 4. Получи API ключи

**Telegram Bot Token:**
- Открой [@BotFather](https://t.me/BotFather) → `/newbot` → скопируй токен

**SeedDance 2.5 (ByteDance):**
- Зарегистрируйся на [volcengine.com](https://www.volcengine.com/)
- Перейди в Visual Intelligence → API Keys
- Скопируй Access Key и Secret Key

**Kling AI:**
- Зарегистрируйся на [platform.klingai.com](https://platform.klingai.com/)
- Перейди в Account → API Keys
- Создай новый ключ (Access Key + Secret Key)

**Luma Dream Machine:**
- Зарегистрируйся на [lumalabs.ai](https://lumalabs.ai/dream-machine/api)
- API → Generate Key

**Runway ML:**
- Зарегистрируйся на [runwayml.com](https://runwayml.com/)
- Account → API Keys

### 5. Запусти бота

```bash
python bot.py
```

---

## Структура проекта

```
tg_video_bot/
├── bot.py                  # Точка входа
├── config.py               # Конфигурация и API ключи
├── requirements.txt
├── .env.example
│
├── handlers/               # Telegram обработчики
│   ├── start.py            # /start, /help
│   ├── generate.py         # Генерация видео (FSM)
│   ├── settings.py         # Настройки провайдера
│   └── history.py          # История генераций
│
├── services/               # API клиенты
│   ├── factory.py          # Единый интерфейс (ProviderFactory)
│   ├── seedance.py         # SeedDance 2.5 (VolcEngine)
│   ├── kling.py            # Kling AI Omni Flash
│   ├── luma.py             # Luma Dream Machine (Flow)
│   └── runway.py           # Runway ML Gen-4
│
├── keyboards/
│   └── kb.py               # Все клавиатуры
│
└── utils/
    ├── storage.py          # JSON хранилище (настройки, история)
    └── middleware.py       # Aiogram middleware (инъекция factory)
```

---

## Использование

1. `/start` — приветствие
2. Нажми **🎬 Генерировать видео**
3. Выбери нейросеть
4. Выбери режим: **Text → Video** или **Image → Video**
5. Выбери длительность и разрешение
6. Введи промпт (на русском или английском)
7. Подтверди → получи видео в чате 🎉

---

## Советы по промптам

- Пиши на **английском** — лучшие результаты у всех провайдеров
- Указывай стиль: `cinematic, 4K, drone shot, slow motion`
- Описывай движение: `camera slowly pans left`, `subject walks forward`
- Примеры хороших промптов:
  - `A futuristic neon city at night, rain, cinematic bokeh, 4K`
  - `Close-up of ocean waves crashing on rocks at sunset, slow motion`
  - `A white cat sleeping on a sofa, sunlight through window, cozy atmosphere`

---

## Production деплой

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t video-bot .
docker run -d --env-file .env video-bot
```

### Systemd service

```ini
[Unit]
Description=AI Video Bot
After=network.target

[Service]
WorkingDirectory=/path/to/tg_video_bot
EnvironmentFile=/path/to/.env
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Лицензия

MIT
