# ⚡ Быстрый старт AGB Searcher

## 🚀 Развертывание за 5 минут

### 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установить Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезайти в систему
exit
# (заново подключиться к серверу)
```

### 2. Клонирование и настройка

```bash
# Клонировать проект
git clone https://github.com/Garanash/agb-searcher.git
cd agb-searcher

# Настроить переменные окружения
cp env.example .env
nano .env
```

**В файле .env укажите:**
```env
POSTGRES_PASSWORD=your_secure_password
POLZA_API_KEY=your_polza_api_key
REACT_APP_API_URL=http://your-server-ip:8000
```

### 3. Запуск

```bash
# Автоматический запуск
chmod +x deploy.sh
./deploy.sh

# ИЛИ ручной запуск
docker-compose -f docker-compose.prod.yml up --build -d
```

### 4. Проверка

```bash
# Проверить статус
docker-compose -f docker-compose.prod.yml ps

# Проверить работу
curl http://localhost:8000/health
curl -I http://localhost
```

## 🌐 Доступ к приложению

- **Frontend**: http://your-server-ip
- **API**: http://your-server-ip:8000
- **Документация API**: http://your-server-ip:8000/docs

## 🔧 Управление

```bash
# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Перезапуск
docker-compose -f docker-compose.prod.yml restart

# Остановка
docker-compose -f docker-compose.prod.yml down

# Обновление
git pull
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📚 Подробная документация

- [SERVER_SETUP.md](SERVER_SETUP.md) - Полная инструкция по развертыванию
- [DEPLOYMENT.md](DEPLOYMENT.md) - Документация по деплою
- [README.md](README.md) - Общая информация о проекте

---

**Готово! 🎉 Ваше приложение запущено и готово к использованию!**
