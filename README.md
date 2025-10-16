# AGB Searcher

Система для актуализации базы данных компаний с использованием Polza.AI API для поиска информации через Perplexity DeepSearch.

## Возможности

- **Поиск информации о компании**: Введите название компании и получите контактную информацию, сайт, адрес, телефон и описание деятельности
- **Поиск компаний по оборудованию**: Найдите компании, которые используют определенное оборудование
- **Массовая загрузка**: Загрузите файл Excel/CSV со списком компаний для автоматического поиска информации
- **База данных компаний**: Просматривайте и редактируйте найденную информацию
- **История поисков**: Отслеживайте все выполненные поиски

## Технологический стек

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React, Ant Design
- **AI**: Polza.AI API (Perplexity DeepSearch)
- **Контейнеризация**: Docker, Docker Compose

## Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git

### Установка и запуск

1. **Клонируйте репозиторий**:
```bash
git clone <repository-url>
cd agb_searcher
```

2. **Запустите приложение**:
```bash
docker-compose up --build
```

3. **Откройте в браузере**:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001
- API документация: http://localhost:8001/docs

### Структура проекта

```
agb_searcher/
├── backend/                 # FastAPI приложение
│   ├── main.py             # Основной файл приложения
│   ├── database.py         # Модели базы данных
│   ├── schemas.py          # Pydantic схемы
│   ├── polza_client.py     # Клиент для Polza.AI API
│   ├── requirements.txt    # Python зависимости
│   └── Dockerfile         # Docker образ для backend
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы приложения
│   │   ├── services/       # API сервисы
│   │   └── App.js          # Основной компонент
│   ├── package.json        # Node.js зависимости
│   └── Dockerfile         # Docker образ для frontend
├── docker-compose.yml      # Конфигурация Docker Compose
└── README.md              # Документация
```

## Использование

### 1. Поиск информации о компании

1. Перейдите на главную страницу
2. Введите название компании
3. Нажмите "Найти информацию"
4. Система найдет контактные данные через Polza.AI

### 2. Поиск компаний по оборудованию

1. Перейдите в раздел "Поиск по оборудованию"
2. Введите название оборудования
3. Получите список компаний, которые его используют

### 3. Массовая загрузка

1. Перейдите в раздел "Массовая загрузка"
2. Подготовьте файл Excel или CSV с названиями компаний в первом столбце
3. Загрузите файл
4. Система автоматически найдет информацию для всех компаний

### 4. Управление базой данных

1. Перейдите в раздел "База компаний"
2. Просматривайте все найденные компании
3. Редактируйте информацию при необходимости

## API Endpoints

### Компании
- `GET /companies` - Получить список компаний
- `GET /companies/{id}` - Получить информацию о компании
- `PUT /companies/{id}` - Обновить информацию о компании
- `POST /companies/search` - Поиск информации о компании
- `POST /companies/bulk-search` - Массовый поиск из файла

### Оборудование
- `GET /equipment` - Получить список оборудования
- `POST /equipment/search` - Поиск компаний по оборудованию

### Логи
- `GET /search-logs` - Получить историю поисков

## Конфигурация

### Переменные окружения

В файле `docker-compose.yml` можно настроить:

- `POLZA_API_KEY` - API ключ от Polza.AI
- `DATABASE_URL` - URL подключения к PostgreSQL
- `REACT_APP_API_URL` - URL backend API для frontend

### Polza.AI API

Приложение использует Polza.AI для доступа к Perplexity DeepSearch. Убедитесь, что у вас есть действующий API ключ.

## Разработка

### Локальная разработка

1. **Backend**:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

2. **Frontend**:
```bash
cd frontend
npm install
npm start
```

3. **База данных**:
```bash
docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15
```

### Добавление новых функций

1. Обновите модели в `backend/database.py`
2. Добавьте схемы в `backend/schemas.py`
3. Создайте API endpoints в `backend/main.py`
4. Обновите frontend компоненты в `frontend/src/`

## Лицензия

MIT License

## Поддержка

При возникновении проблем:
1. Проверьте логи Docker: `docker-compose logs`
2. Убедитесь, что API ключ Polza.AI действителен
3. Проверьте подключение к базе данных
