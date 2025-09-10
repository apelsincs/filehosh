#!/bin/bash

# 🚀 Автоматизированное развертывание на Beget VPS
# Использование: ./deploy_beget.sh

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_DIR="/home/pasynkun/222_ru_fl"
SERVICE_USER="pasynkun"
SERVICE_GROUP="pasynkun"
DB_NAME="filehost"
DB_USER="filehost_user"
DB_PASSWORD="$(openssl rand -base64 32)"  # Генерируем случайный пароль

echo -e "${BLUE}🚀 Начинаем развертывание на Beget VPS...${NC}"

# Проверка прав sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Этот скрипт должен выполняться с правами sudo${NC}"
    exit 1
fi

# Проверка существования проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Директория проекта не найдена: $PROJECT_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Обновление системы...${NC}"
apt update
apt upgrade -y

echo -e "${YELLOW}📦 Установка системных пакетов...${NC}"
apt install -y \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    libpq-dev \
    python3-dev \
    fail2ban \
    ufw

echo -e "${YELLOW}🗄️ Настройка PostgreSQL...${NC}"
# Создание базы данных и пользователя
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"

# Включение и запуск PostgreSQL
systemctl enable postgresql
systemctl start postgresql

echo -e "${YELLOW}🔴 Настройка Redis...${NC}"
systemctl enable redis
systemctl start redis

echo -e "${YELLOW}🐍 Настройка Python окружения...${NC}"
cd "$PROJECT_DIR"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
echo -e "${YELLOW}📦 Установка Python зависимостей...${NC}"
pip install -r requirements-prod.txt

echo -e "${YELLOW}⚙️ Создание .env файла...${NC}"
# Генерация SECRET_KEY
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Создание .env файла
cat > .env << EOF
# Django settings
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=pasynkun.beget.tech,localhost,127.0.0.1

# Database
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# File settings
FILE_EXPIRY_HOURS=24
MAX_FILE_SIZE=100
QR_CODE_SIZE=10

# Security
CSRF_TRUSTED_ORIGINS=https://pasynkun.beget.tech

# Optional: Sentry (для мониторинга ошибок)
# SENTRY_DSN=your_sentry_dsn_here
EOF

echo -e "${GREEN}✅ .env файл создан с паролем БД: $DB_PASSWORD${NC}"

echo -e "${YELLOW}🗄️ Применение миграций...${NC}"
python manage.py migrate --settings=filehost.settings_prod

echo -e "${YELLOW}📁 Сбор статических файлов...${NC}"
python manage.py collectstatic --settings=filehost.settings_prod --noinput

echo -e "${YELLOW}🔧 Настройка Gunicorn...${NC}"
# Создание директорий для логов
mkdir -p /var/log/gunicorn /var/log/celery /var/run/celery
chown $SERVICE_USER:$SERVICE_GROUP /var/log/gunicorn /var/log/celery /var/run/celery

# Копирование конфигураций
cp gunicorn.conf.py "$PROJECT_DIR/"
cp filehost/celery.py "$PROJECT_DIR/"
chown $SERVICE_USER:$SERVICE_GROUP "$PROJECT_DIR/gunicorn.conf.py" "$PROJECT_DIR/celery.py"

echo -e "${YELLOW}⚙️ Настройка systemd сервисов...${NC}"
# Копирование файлов сервисов
cp filehost.service /etc/systemd/system/
cp celery.service /etc/systemd/system/
cp celerybeat.service /etc/systemd/system/

# Перезагрузка systemd
systemctl daemon-reload

# Включение сервисов
systemctl enable filehost celery celerybeat

echo -e "${YELLOW}🌐 Настройка Nginx...${NC}"
# Копирование конфигурации Nginx
cp nginx.conf /etc/nginx/sites-available/filehost
ln -sf /etc/nginx/sites-available/filehost /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации Nginx
nginx -t

echo -e "${YELLOW}🔒 Настройка безопасности...${NC}"
# Настройка UFW
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Настройка Fail2ban
systemctl enable fail2ban
systemctl start fail2ban

echo -e "${YELLOW}🚀 Запуск сервисов...${NC}"
# Запуск всех сервисов
systemctl start filehost celery celerybeat nginx

echo -e "${YELLOW}✅ Проверка статуса сервисов...${NC}"
# Проверка статуса
echo -e "${BLUE}📊 Статус сервисов:${NC}"
systemctl status filehost --no-pager
systemctl status celery --no-pager
systemctl status celerybeat --no-pager
systemctl status nginx --no-pager
systemctl status postgresql --no-pager
systemctl status redis --no-pager

echo -e "${GREEN}🎉 Развертывание завершено!${NC}"
echo -e "${BLUE}📋 Информация о развертывании:${NC}"
echo -e "🌐 Сайт: http://pasynkun.beget.tech/"
echo -e "🗄️ База данных: $DB_NAME"
echo -e "👤 Пользователь БД: $DB_USER"
echo -e "🔑 Пароль БД: $DB_PASSWORD"
echo -e "📁 Проект: $PROJECT_DIR"
echo -e "🐍 Виртуальное окружение: $PROJECT_DIR/venv"

echo -e "${YELLOW}🔧 Полезные команды:${NC}"
echo -e "Проверка логов: sudo journalctl -u filehost -f"
echo -e "Перезапуск: sudo systemctl restart filehost celery celerybeat nginx"
echo -e "Статус: sudo systemctl status filehost celery celerybeat nginx"

echo -e "${GREEN}✅ Все готово! Файловый хостинг запущен и доступен.${NC}"
