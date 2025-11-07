# 🔧 Исправление ошибки "JavaScript heap out of memory"

## Проблема
Ошибка возникает из-за нехватки памяти при сборке React приложения в Docker контейнере.

## 🚀 Быстрое решение

### Вариант 1: Автоматическое исправление

```bash
# На сервере выполните:
git pull
chmod +x fix-memory-issue.sh
./fix-memory-issue.sh
```

### Вариант 2: Ручное исправление

```bash
# 1. Обновить код
git pull

# 2. Очистить Docker кэш
docker system prune -f

# 3. Пересобрать с увеличенной памятью
docker-compose -f docker-compose.prod.yml build --no-cache frontend

# 4. Запустить
docker-compose -f docker-compose.prod.yml up -d
```

### Вариант 3: Сборка с максимальной памятью

```bash
# 1. Обновить код
git pull

# 2. Собрать frontend с увеличенной памятью
cd frontend
docker build -f Dockerfile.prod.memory \
  --build-arg NODE_OPTIONS="--max-old-space-size=6144" \
  -t agb-searcher-frontend-memory .

# 3. Вернуться в корневую папку
cd ..

# 4. Запустить все сервисы
docker-compose -f docker-compose.prod.yml up -d
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

1. **Увеличен лимит памяти Node.js** - `NODE_OPTIONS="--max-old-space-size=4096"`
2. **Создан оптимизированный Dockerfile** - `Dockerfile.prod.memory`
3. **Добавлены переменные окружения** для оптимизации сборки
4. **Обновлен docker-compose.prod.yml** - использует новый Dockerfile
5. **Добавлен скрипт исправления** - `fix-memory-issue.sh`

## ⚠️ Если проблема остается

### Увеличить память сервера
```bash
# Проверить доступную память
free -h

# Если памяти меньше 2GB, рассмотрите:
# 1. Увеличение RAM сервера
# 2. Использование swap файла
```

### Создать swap файл (если памяти мало)
```bash
# Создать swap файл 2GB
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Сделать постоянным
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Альтернативный подход - сборка на хосте
```bash
# 1. Установить Node.js на сервере
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 2. Собрать приложение локально
cd frontend
npm install
NODE_OPTIONS="--max-old-space-size=4096" npm run build

# 3. Создать простой Dockerfile для готового build
cat > Dockerfile.simple << EOF
FROM nginx:alpine
COPY build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# 4. Собрать образ
docker build -f Dockerfile.simple -t agb-searcher-frontend-simple .
```

## 🎯 Ожидаемый результат

После исправления:
- ✅ Frontend контейнер успешно собирается
- ✅ Приложение доступно по http://your-server-ip
- ✅ API работает на http://your-server-ip:8000
- ✅ Markdown форматирование работает в чате
- ✅ Нет ошибок "heap out of memory"

## 📊 Мониторинг памяти

```bash
# Проверить использование памяти контейнерами
docker stats

# Проверить использование памяти системой
free -h

# Проверить процессы с наибольшим потреблением памяти
ps aux --sort=-%mem | head -10
```
