# 🔧 Исправление ошибки package-lock.json на сервере

## Проблема
Ошибка возникает из-за несоответствия между `package.json` и `package-lock.json` после добавления новых зависимостей (`react-markdown`, `remark-gfm`).

## 🚀 Быстрое решение

### Вариант 1: Автоматическое исправление

```bash
# На сервере выполните:
git pull
chmod +x fix-package-lock.sh
./fix-package-lock.sh
docker-compose -f docker-compose.prod.yml up --build -d
```

### Вариант 2: Ручное исправление

```bash
# 1. Обновить код
git pull

# 2. Перейти в папку frontend
cd frontend

# 3. Удалить проблемные файлы
rm -rf node_modules
rm -f package-lock.json

# 4. Установить зависимости заново
npm install

# 5. Вернуться в корневую папку
cd ..

# 6. Пересобрать и запустить
docker-compose -f docker-compose.prod.yml up --build -d
```

### Вариант 3: Полная пересборка

```bash
# 1. Остановить все контейнеры
docker-compose -f docker-compose.prod.yml down

# 2. Удалить все образы
docker system prune -a -f

# 3. Обновить код
git pull

# 4. Пересобрать с нуля
docker-compose -f docker-compose.prod.yml up --build -d
```

## 🔍 Проверка результата

```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверить логи frontend
docker-compose -f docker-compose.prod.yml logs frontend

# Проверить работу приложения
curl -I http://localhost
curl http://localhost:8000/health
```

## 📋 Что было исправлено

1. **Обновлен Dockerfile.prod** - использует `npm install` вместо `npm ci`
2. **Создан Dockerfile.prod.alt** - с полной очисткой перед установкой
3. **Обновлен docker-compose.prod.yml** - использует альтернативный Dockerfile
4. **Добавлен скрипт fix-package-lock.sh** - для автоматического исправления

## ⚠️ Если проблема остается

Если ошибка все еще возникает, попробуйте:

```bash
# Очистить Docker кэш
docker builder prune -a -f

# Пересобрать только frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

## 🎯 Ожидаемый результат

После исправления:
- ✅ Frontend контейнер успешно собирается
- ✅ Приложение доступно по http://your-server-ip
- ✅ API работает на http://your-server-ip:8000
- ✅ Markdown форматирование работает в чате
