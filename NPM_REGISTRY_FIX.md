# 🔧 Исправление проблем с npm registry

## Проблема
Ошибки возникают из-за использования китайского npm registry (`registry.npmmirror.com`), который возвращает поврежденные пакеты.

## 🚀 Быстрое решение

### Вариант 1: Автоматическое исправление

```bash
# На сервере выполните:
git pull
chmod +x fix-npm-registry.sh
./fix-npm-registry.sh
docker-compose up --build
```

### Вариант 2: Ручное исправление

```bash
# 1. Обновить код
git pull

# 2. Установить правильный npm registry
npm config set registry https://registry.npmjs.org/

# 3. Очистить npm кэш
npm cache clean --force

# 4. Пересобрать
docker-compose up --build
```

### Вариант 3: Исправление в Docker

```bash
# 1. Обновить код
git pull

# 2. Очистить Docker кэш
docker system prune -f

# 3. Пересобрать с новым Dockerfile
docker-compose up --build --no-cache
```

## 🔍 Проверка результата

```bash
# Проверить npm registry
npm config get registry

# Проверить статус контейнеров
docker-compose ps

# Проверить работу приложения
curl -I http://localhost:3000
curl http://localhost:8000/health
```

## 📋 Что было исправлено

1. **Добавлен .npmrc файл** - настройки для правильного registry
2. **Обновлены все Dockerfile'ы** - добавлена настройка npm registry
3. **Создан скрипт исправления** - `fix-npm-registry.sh`
4. **Добавлена очистка кэша** - для удаления поврежденных пакетов

## ⚠️ Если проблема остается

### Очистить все кэши

```bash
# Очистить npm кэш
npm cache clean --force

# Очистить Docker кэш
docker system prune -a -f

# Удалить node_modules
rm -rf frontend/node_modules frontend/package-lock.json

# Пересобрать
docker-compose up --build --no-cache
```

### Использовать другой registry

```bash
# Попробовать другой registry
npm config set registry https://registry.yarnpkg.com/

# Или использовать yarn вместо npm
npm install -g yarn
yarn config set registry https://registry.npmjs.org/
```

### Проверить сетевое соединение

```bash
# Проверить доступность npm registry
curl -I https://registry.npmjs.org/

# Проверить DNS
nslookup registry.npmjs.org
```

## 🎯 Ожидаемый результат

После исправления:
- ✅ npm install работает без ошибок
- ✅ Frontend контейнер успешно собирается
- ✅ Приложение доступно по http://localhost:3000
- ✅ API работает на http://localhost:8000
- ✅ Нет ошибок "TAR_ENTRY_INVALID" или "400 Bad Request"
