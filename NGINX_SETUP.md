# 🌐 Настройка приложения без порта

## Проблема
Приложение сейчас доступно по адресу `http://188.225.56.200:3000`, но нужно сделать его доступным по `http://188.225.56.200` без указания порта.

## 🚀 Решение: Nginx Reverse Proxy

### Вариант 1: Автоматическое переключение (рекомендуется)

```bash
# На сервере выполните:
git pull
chmod +x switch-config.sh
./switch-config.sh nginx
```

### Вариант 2: Ручное переключение

```bash
# 1. Обновить код
git pull

# 2. Остановить текущие контейнеры
docker-compose down

# 3. Запустить с Nginx
docker-compose -f docker-compose.nginx.yml up --build -d
```

## 🔧 Что изменилось

### 1. **Nginx Reverse Proxy**
- Nginx слушает порт 80 (стандартный HTTP порт)
- Маршрутизирует запросы к frontend и backend
- Обрабатывает CORS автоматически

### 2. **Новые URL**
- **Frontend:** `http://188.225.56.200` (без порта!)
- **API:** `http://188.225.56.200/api` (префикс /api)
- **Health Check:** `http://188.225.56.200/health`

### 3. **Конфигурации**
- `docker-compose.yml` - прямая работа с портами
- `docker-compose.nginx.yml` - через Nginx reverse proxy
- `switch-config.sh` - скрипт переключения между конфигурациями

## 📋 Структура маршрутизации

```
http://188.225.56.200/
├── / (frontend) → React приложение
├── /api/ → Backend API
│   ├── /api/companies
│   ├── /api/chat
│   ├── /api/dialogs
│   └── ...
└── /health → Health check
```

## 🔄 Переключение между конфигурациями

### Nginx (без порта)
```bash
./switch-config.sh nginx
# Доступ: http://188.225.56.200
```

### Прямая работа (с портами)
```bash
./switch-config.sh direct
# Доступ: http://188.225.56.200:3000
```

## ⚙️ Настройки Nginx

### Основные возможности:
- ✅ Reverse proxy для frontend и backend
- ✅ Автоматическая обработка CORS
- ✅ Сжатие gzip для статических файлов
- ✅ Кэширование статических ресурсов
- ✅ Rate limiting для API
- ✅ Security headers
- ✅ WebSocket поддержка

### Конфигурация:
- Файл: `nginx.conf`
- Проксирует `/api/` → backend:8000
- Проксирует `/` → frontend:3000
- Обрабатывает CORS заголовки

## 🎯 Ожидаемый результат

После переключения на Nginx:
- ✅ Приложение доступно по `http://188.225.56.200`
- ✅ API работает по `http://188.225.56.200/api`
- ✅ Нет CORS ошибок
- ✅ Все функции работают корректно
- ✅ Статические файлы кэшируются
- ✅ Улучшена производительность

## 🔍 Проверка работы

```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.nginx.yml ps

# Проверить логи
docker-compose -f docker-compose.nginx.yml logs nginx
docker-compose -f docker-compose.nginx.yml logs frontend
docker-compose -f docker-compose.nginx.yml logs backend

# Тестировать доступность
curl -I http://188.225.56.200
curl http://188.225.56.200/health
curl http://188.225.56.200/api/health
```

## 🚨 Если что-то не работает

### Откат к прямой конфигурации:
```bash
./switch-config.sh direct
```

### Проверка логов:
```bash
docker-compose -f docker-compose.nginx.yml logs -f
```

### Перезапуск Nginx:
```bash
docker-compose -f docker-compose.nginx.yml restart nginx
```
