# AGB Searcher

Система поиска информации о компаниях с AI-помощником и поддержкой Markdown форматирования.

## 🚀 Основные возможности

- **AI-чат** - главная страница с умным помощником
- **Поиск компаний** - поиск по названию компании
- **Поиск по оборудованию** - поиск компаний по типу оборудования
- **База данных компаний** - просмотр сохраненных компаний
- **Настройки диалогов** - конфигурация AI помощников
- **Markdown форматирование** - красивое отображение ответов AI
- **Выбор помощников** - предустановленные AI-боты с разными ролями

## 🛠 Технологии

- **Frontend**: React, Ant Design, React Markdown
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI**: Polza.AI API
- **Deployment**: Docker, Docker Compose, Nginx

## 🏃‍♂️ Быстрый старт

### Локальная разработка

1. **Клонируйте репозиторий**
   ```bash
   git clone <your-repo-url>
   cd agb-searcher
   ```

2. **Запустите с Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Откройте приложение**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Production деплой

См. [DEPLOYMENT.md](DEPLOYMENT.md) для подробных инструкций по деплою на Debian сервер.

## 📁 Структура проекта

```
agb-searcher/
├── frontend/                 # React приложение
│   ├── src/
│   │   ├── pages/           # Страницы приложения
│   │   ├── services/        # API сервисы
│   │   └── App.js          # Главный компонент
│   ├── Dockerfile          # Development Dockerfile
│   ├── Dockerfile.prod     # Production Dockerfile
│   └── nginx.conf          # Nginx конфигурация
├── backend/                 # FastAPI приложение
│   ├── main.py            # Главный файл API
│   ├── polza_client.py    # Клиент для Polza.AI
│   ├── database.py        # Модели базы данных
│   ├── schemas.py         # Pydantic схемы
│   └── Dockerfile         # Backend Dockerfile
├── docker-compose.yml      # Development конфигурация
├── docker-compose.prod.yml # Production конфигурация
├── deploy.sh              # Скрипт деплоя
├── env.example            # Пример переменных окружения
└── DEPLOYMENT.md          # Инструкции по деплою
```

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `env.example`:

```env
# Database
POSTGRES_PASSWORD=your_secure_password

# Polza.AI API
POLZA_API_KEY=your_polza_api_key

# Application URLs
REACT_APP_API_URL=http://localhost:8000
```

## 🎯 Использование

### AI-чат (Главная страница)

1. **Выберите помощника** из выпадающего списка
2. **Задайте вопрос** в поле ввода
3. **Получите ответ** в красивом Markdown формате
4. **Создайте новый диалог** для новой темы

### Поиск компаний

1. Перейдите в "Поиск компании"
2. Введите название компании
3. Получите информацию о контактах и деятельности

### Настройка помощников

1. Перейдите в "Настройки диалогов"
2. Создайте нового помощника с:
   - Названием и описанием
   - Системным промптом
   - Моделью AI
   - Параметрами (температура, токены)

## 📊 API Endpoints

- `GET /` - Информация об API
- `GET /health` - Health check
- `POST /chat` - Чат с AI
- `POST /chat/dialog` - Чат с сохранением диалога
- `GET /companies/search` - Поиск компаний
- `GET /equipment/search` - Поиск по оборудованию
- `GET /assistants` - Список помощников
- `GET /models` - Доступные модели AI

Полная документация API: http://localhost:8000/docs

## 🚀 Деплой на сервер

### Автоматический деплой

```bash
# На Debian сервере
./deploy.sh
```

### Ручной деплой

```bash
# Production
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔍 Мониторинг

### Проверка статуса
```bash
docker-compose ps
```

### Просмотр логов
```bash
docker-compose logs -f
```

### Health check
```bash
curl http://localhost:8000/health
```

## 🛡 Безопасность

- Все пароли хранятся в переменных окружения
- CORS настроен для безопасного взаимодействия
- Nginx конфигурация включает security headers
- Рекомендуется использовать HTTPS в production

## 📝 Лицензия

MIT License

## 🤝 Поддержка

Для вопросов и поддержки создайте issue в репозитории.