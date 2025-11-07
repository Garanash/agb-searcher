# 🚀 Полная инструкция по развертыванию AGB Searcher на голом сервере

## 📋 Требования к серверу

- **ОС**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **RAM**: Минимум 2GB (рекомендуется 4GB+)
- **CPU**: 2 ядра (рекомендуется 4+)
- **Диск**: Минимум 20GB свободного места
- **Сеть**: Доступ в интернет для загрузки зависимостей

## 🔧 Шаг 1: Подготовка сервера

### Обновление системы

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
# или для новых версий
sudo dnf update -y
```

### Установка необходимых пакетов

```bash
# Ubuntu/Debian
sudo apt install -y curl wget git unzip software-properties-common

# CentOS/RHEL
sudo yum install -y curl wget git unzip
# или
sudo dnf install -y curl wget git unzip
```

## 🐳 Шаг 2: Установка Docker

### Автоматическая установка (рекомендуется)

```bash
# Скачать и запустить официальный скрипт установки
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Включить автозапуск Docker
sudo systemctl enable docker
sudo systemctl start docker

# Проверить установку
docker --version
```

### Ручная установка (Ubuntu/Debian)

```bash
# Удалить старые версии
sudo apt remove docker docker-engine docker.io containerd runc

# Установить зависимости
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Добавить официальный GPG ключ Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Добавить репозиторий Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Обновить пакеты и установить Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
```

## 🐙 Шаг 3: Установка Docker Compose

```bash
# Скачать последнюю версию Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Сделать исполняемым
sudo chmod +x /usr/local/bin/docker-compose

# Создать символическую ссылку
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Проверить установку
docker-compose --version
```

## 🔐 Шаг 4: Настройка безопасности

### Настройка файрвола

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Создание пользователя для приложения (опционально)

```bash
# Создать пользователя
sudo adduser agbuser
sudo usermod -aG docker agbuser

# Переключиться на пользователя
sudo su - agbuser
```

## 📥 Шаг 5: Клонирование проекта

```bash
# Клонировать репозиторий
git clone https://github.com/Garanash/agb-searcher.git
cd agb-searcher

# Проверить права доступа
ls -la
```

## ⚙️ Шаг 6: Настройка переменных окружения

```bash
# Скопировать пример файла окружения
cp env.example .env

# Отредактировать файл окружения
nano .env
```

### Содержимое файла .env:

```env
# Database configuration
POSTGRES_PASSWORD=your_very_secure_password_here_123

# Polza.AI API configuration
POLZA_API_KEY=your_polza_api_key_from_polza_ai

# Application URLs
REACT_APP_API_URL=http://your-server-ip:8000
```

**Важно**: 
- Замените `your_very_secure_password_here_123` на надежный пароль
- Получите API ключ на https://polza.ai
- Замените `your-server-ip` на IP адрес вашего сервера

## 🚀 Шаг 7: Развертывание приложения

### Автоматическое развертывание (рекомендуется)

```bash
# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запустить развертывание
./deploy.sh
```

### Ручное развертывание

```bash
# Собрать и запустить контейнеры
docker-compose -f docker-compose.prod.yml up --build -d

# Проверить статус
docker-compose -f docker-compose.prod.yml ps

# Просмотреть логи
docker-compose -f docker-compose.prod.yml logs -f
```

## ✅ Шаг 8: Проверка работы

### Проверка сервисов

```bash
# Проверить статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Проверить логи
docker-compose -f docker-compose.prod.yml logs

# Проверить health check
curl http://localhost:8000/health
```

### Проверка доступности

```bash
# Frontend (должен вернуть HTML)
curl -I http://localhost

# Backend API (должен вернуть JSON)
curl http://localhost:8000

# API документация
curl http://localhost:8000/docs
```

## 🌐 Шаг 9: Настройка домена (опционально)

### Установка Nginx (если не используется Docker)

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
# или
sudo dnf install -y nginx
```

### Конфигурация Nginx

```bash
# Создать конфигурацию
sudo nano /etc/nginx/sites-available/agb-searcher
```

Содержимое файла:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        proxy_pass http://localhost;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активировать конфигурацию
sudo ln -s /etc/nginx/sites-available/agb-searcher /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

## 🔒 Шаг 10: Настройка SSL (рекомендуется)

### Установка Certbot

```bash
# Ubuntu/Debian
sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx
# или
sudo dnf install -y certbot python3-certbot-nginx
```

### Получение SSL сертификата

```bash
# Получить сертификат
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Настроить автообновление
sudo crontab -e
# Добавить строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Шаг 11: Мониторинг и обслуживание

### Полезные команды

```bash
# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Перезапуск сервисов
docker-compose -f docker-compose.prod.yml restart

# Обновление приложения
git pull
docker-compose -f docker-compose.prod.yml up --build -d

# Очистка неиспользуемых образов
docker system prune -f

# Резервное копирование базы данных
docker exec agb-searcher-postgres-prod pg_dump -U agb_user agb_searcher > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Мониторинг ресурсов

```bash
# Использование ресурсов Docker
docker stats

# Использование диска
df -h

# Использование памяти
free -h

# Загрузка системы
htop
# или
top
```

## 🛠 Устранение неполадок

### Проблемы с Docker

```bash
# Проверить статус Docker
sudo systemctl status docker

# Перезапустить Docker
sudo systemctl restart docker

# Проверить логи Docker
sudo journalctl -u docker.service
```

### Проблемы с приложением

```bash
# Проверить логи приложения
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Перезапустить конкретный сервис
docker-compose -f docker-compose.prod.yml restart backend

# Проверить подключение к базе данных
docker exec -it agb-searcher-postgres-prod psql -U agb_user -d agb_searcher
```

### Проблемы с сетью

```bash
# Проверить открытые порты
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :8000

# Проверить файрвол
sudo ufw status
# или
sudo firewall-cmd --list-all
```

## 📈 Оптимизация производительности

### Настройка Docker

```bash
# Создать файл конфигурации Docker
sudo nano /etc/docker/daemon.json
```

Содержимое:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

```bash
# Перезапустить Docker
sudo systemctl restart docker
```

### Настройка системы

```bash
# Увеличить лимиты файлов
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Оптимизировать сетевые параметры
echo "net.core.somaxconn = 65535" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65535" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 🎯 Финальная проверка

После выполнения всех шагов ваше приложение должно быть доступно по адресу:

- **Frontend**: http://your-server-ip
- **Backend API**: http://your-server-ip:8000
- **API Documentation**: http://your-server-ip:8000/docs

### Тестовые команды

```bash
# Проверить health check
curl http://your-server-ip:8000/health

# Проверить frontend
curl -I http://your-server-ip

# Проверить API
curl http://your-server-ip:8000
```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker-compose -f docker-compose.prod.yml logs`
2. Проверьте статус сервисов: `docker-compose -f docker-compose.prod.yml ps`
3. Проверьте переменные окружения в файле `.env`
4. Убедитесь, что все порты открыты в файрволе

---

**Поздравляем! 🎉 Ваше приложение AGB Searcher успешно развернуто на сервере!**
