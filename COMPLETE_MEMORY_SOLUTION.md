# 🚨 Полное решение проблем с памятью при сборке React

## Проблема
Сервер не имеет достаточно памяти для сборки React приложения в Docker контейнере.

## 🚀 Решения (по приоритету)

### 1. Автоматическое решение (рекомендуется)

```bash
# На сервере выполните:
git pull
chmod +x solve-memory-issues.sh
./solve-memory-issues.sh
```

Этот скрипт попробует все возможные решения автоматически.

### 2. Сборка на хосте (самое надежное)

```bash
# 1. Обновить код
git pull

# 2. Установить Node.js (если не установлен)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 3. Собрать приложение на хосте
chmod +x build-on-host.sh
./build-on-host.sh

# 4. Запустить с минимальным Docker
docker-compose -f docker-compose.minimal.yml up -d
```

### 3. Создание swap файла

```bash
# Создать swap файл 4GB
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Сделать постоянным
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Проверить
free -h

# Пересобрать
docker-compose -f docker-compose.prod.yml up --build -d
```

### 4. Увеличение лимитов Docker

```bash
# Создать или обновить /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  },
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# Перезапустить Docker
sudo systemctl restart docker

# Пересобрать
docker-compose -f docker-compose.prod.yml up --build -d
```

### 5. Сборка на другом сервере

Если ничего не помогает, соберите на более мощном сервере:

```bash
# На мощном сервере:
git clone https://github.com/Garanash/agb-searcher.git
cd agb-searcher
cp env.example .env
# Отредактируйте .env
docker-compose -f docker-compose.prod.yml up --build -d

# Скопируйте готовый build на целевой сервер:
docker save agb-searcher-frontend-prod | gzip > frontend.tar.gz
# Перенесите frontend.tar.gz на целевой сервер

# На целевом сервере:
docker load < frontend.tar.gz
docker-compose -f docker-compose.prod.yml up -d
```

## 🔍 Проверка результата

```bash
# Проверить статус
docker-compose -f docker-compose.prod.yml ps
# или
docker-compose -f docker-compose.minimal.yml ps

# Проверить работу
curl -I http://localhost
curl http://localhost:8000/health

# Проверить память
free -h
docker stats
```

## 📊 Мониторинг ресурсов

```bash
# Использование памяти
free -h

# Использование swap
swapon --show

# Процессы с наибольшим потреблением памяти
ps aux --sort=-%mem | head -10

# Docker статистика
docker stats --no-stream
```

## ⚠️ Если все решения не помогают

### Вариант A: Увеличить RAM сервера
- Минимум: 4GB RAM
- Рекомендуется: 8GB+ RAM

### Вариант B: Использовать более мощный сервер для сборки
1. Собрать на мощном сервере
2. Экспортировать готовый образ
3. Импортировать на целевой сервер

### Вариант C: Использовать CI/CD
Настроить автоматическую сборку в GitHub Actions или другом CI/CD сервисе.

## 🎯 Ожидаемый результат

После применения любого из решений:
- ✅ Frontend контейнер успешно собирается
- ✅ Приложение доступно по http://your-server-ip
- ✅ API работает на http://your-server-ip:8000
- ✅ Markdown форматирование работает в чате
- ✅ Нет ошибок "out of memory"

## 📋 Резюме решений

1. **Автоматический скрипт** - `solve-memory-issues.sh`
2. **Сборка на хосте** - `build-on-host.sh` + `docker-compose.minimal.yml`
3. **Swap файл** - для серверов с < 4GB RAM
4. **Увеличение лимитов Docker** - для контейнеров
5. **Сборка на другом сервере** - для очень слабых серверов

Выберите подходящий вариант в зависимости от ваших ресурсов!
