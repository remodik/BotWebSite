# remod3Bot Dashboard

Современная панель управления Discord ботом с дизайном в стиле Juniper.bot.

## 🎨 Особенности

- ✨ Современный дизайн с градиентами и анимациями
- 📱 Полностью responsive (адаптивный) дизайн
- 🎯 Боковая панель навигации
- 🔐 OAuth2 авторизация через Discord
- ⚙️ Управление префиксами команд
- 👥 Настройка модераторов и администраторов
- 📊 Статистика системы
- 🎨 Карточки серверов с hover эффектами

## 📋 Требования

- Python 3.11+
- Discord Application (Client ID, Client Secret, Bot Token)

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните `.env` вашими данными:

```env
DISCORD_CLIENT_ID=ваш_client_id
DISCORD_CLIENT_SECRET=ваш_client_secret
DISCORD_REDIRECT_URI=http://localhost:8000/auth
DISCORD_API_URL=https://discord.com/api/v10
BOT_TOKEN=ваш_bot_token
PREFIXES_FILE=json/prefixes.json
```

### 3. Создание необходимых директорий

```bash
mkdir -p json
```

### 4. Запуск приложения

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Приложение будет доступно по адресу: `http://localhost:8000`

## 📁 Структура проекта

```
/app/
├── templates/          # HTML шаблоны
│   ├── index.html     # Главная страница
│   ├── dashboard.html # Панель управления
│   ├── guild.html     # Настройки сервера
│   └── stats.html     # Статистика
├── static/            # Статические файлы
│   └── styles.css     # Дополнительные стили
├── json/              # JSON файлы с данными
│   ├── guild_settings.json
│   └── prefixes.json
├── main.py            # Главный файл приложения
├── .env               # Переменные окружения
└── requirements.txt   # Зависимости Python
```

## 🎯 Основные маршруты

- `/` - Главная страница
- `/login` - Авторизация через Discord
- `/dashboard` - Панель управления серверами
- `/guild/{guild_id}` - Настройки конкретного сервера
- `/stats` - Статистика системы

## 🎨 Дизайн система

### Цветовая палитра

```css
--primary: #5865F2        /* Discord blue */
--primary-dark: #4752C4   
--secondary: #2C2F33      /* Dark gray */
--dark: #1E2124          
--darker: #16191C         /* Almost black */
--success: #43B581        /* Green */
--danger: #F04747         /* Red */
--warning: #FAA61A        /* Orange */
```

### Градиенты

- Primary: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- Success: `linear-gradient(135deg, #43B581 0%, #11998e 100%)`

### Типографика

- Font Family: Poppins (Google Fonts)
- Weights: 300, 400, 500, 600, 700, 800

## 🔧 Настройка Discord Application

1. Перейдите на [Discord Developer Portal](https://discord.com/developers/applications)
2. Создайте новое приложение
3. В разделе "OAuth2" добавьте redirect URI: `http://localhost:8000/auth`
4. В разделе "Bot" создайте бота и получите токен
5. Скопируйте Client ID, Client Secret и Bot Token в `.env`

## 📝 Функционал

### Управление префиксами
- Настройка уникальных префиксов для каждого сервера
- Мгновенное применение изменений

### Модерация
- Настройка каналов для логов
- Управление администраторами и модераторами
- Система уведомлений

### Статистика
- Отслеживание посещений
- Активные пользователи
- Время работы системы

## 🤝 Вклад в проект

Если вы хотите внести свой вклад:

1. Fork проекта
2. Создайте ветку для новой функции (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

## 👨‍💻 Автор

remod3Bot Team

## 🙏 Благодарности

- Дизайн вдохновлен [Juniper.bot](https://juniper.bot/)
- Icons by [Font Awesome](https://fontawesome.com/)
- Fonts by [Google Fonts](https://fonts.google.com/)
