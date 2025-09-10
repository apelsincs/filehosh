# 🚀 Развертывание на Beget VPS (pasynkun.beget.tech)

## 📋 Подготовка к развертыванию

### 1. Подключение к серверу
```bash
ssh pasynkun@pasynkun.beget.tech
# Пароль: Msl3TPA3cWJR
```

### 2. Проверка текущего состояния
```bash
# Проверить, что репозиторий скопирован
ls -la
cd 222_ru_fl  # или как называется папка с проектом

# Проверить Python версию
python3 --version
python3 -m pip --version
```

## 🔧 Установка зависимостей

### 1. Обновление системы
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Установка системных пакетов
```bash
sudo apt install -y \
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
    python3-dev
```

### 3. Настройка PostgreSQL
```bash
# Переключиться на пользователя postgres
sudo -u postgres psql

# Создать базу данных и пользователя
CREATE DATABASE filehost;
CREATE USER filehost_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE filehost TO filehost_user;
ALTER USER filehost_user CREATEDB;
\q

# Включить и запустить PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 4. Настройка Redis
```bash
# Redis уже установлен и запущен
sudo systemctl enable redis
sudo systemctl start redis
sudo systemctl status redis
```

## 🐍 Настройка Python окружения

### 1. Создание виртуального окружения
```bash
cd /home/pasynkun/222_ru_fl  # или путь к вашему проекту
python3 -m venv venv
source venv/bin/activate
```

### 2. Установка зависимостей
```bash
# Обновить pip
pip install --upgrade pip

# Установить production зависимости
pip install -r requirements-prod.txt
```

### 3. Создание .env файла
```bash
# Скопировать пример
cp env.production .env

# Отредактировать .env файл
nano .env
```

**Содержимое .env файла:**
```env
# Django settings
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
ALLOWED_HOSTS=pasynkun.beget.tech,localhost,127.0.0.1

# Database
DB_NAME=filehost
DB_USER=filehost_user
DB_PASSWORD=your_secure_password_here
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
```

## 🗄️ Настройка базы данных

### 1. Применение миграций
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Применить миграции
python manage.py migrate --settings=filehost.settings_prod

# Создать суперпользователя (опционально)
python manage.py createsuperuser --settings=filehost.settings_prod
```

### 2. Сбор статических файлов
```bash
python manage.py collectstatic --settings=filehost.settings_prod --noinput
```

## 🔧 Настройка Gunicorn

### 1. Создание директорий для логов
```bash
sudo mkdir -p /var/log/gunicorn /var/log/celery /var/run/celery
sudo chown pasynkun:pasynkun /var/log/gunicorn /var/log/celery /var/run/celery
```

### 2. Настройка systemd сервисов
```bash
# Скопировать файлы сервисов
sudo cp filehost.service /etc/systemd/system/
sudo cp celery.service /etc/systemd/system/
sudo cp celerybeat.service /etc/systemd/system/

# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить сервисы
sudo systemctl enable filehost celery celerybeat
```

### 3. Запуск сервисов
```bash
sudo systemctl start filehost celery celerybeat
sudo systemctl status filehost celery celerybeat
```

## 🌐 Настройка Nginx

### 1. Создание конфигурации Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/filehost
sudo ln -s /etc/nginx/sites-available/filehost /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # удалить дефолтный сайт
```

### 2. Проверка и перезапуск Nginx
```bash
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🔒 Настройка безопасности

### 1. Настройка UFW (firewall)
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 2. Настройка Fail2ban
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 🚀 Запуск и тестирование

### 1. Проверка всех сервисов
```bash
sudo systemctl status filehost
sudo systemctl status celery
sudo systemctl status celerybeat
sudo systemctl status nginx
sudo systemctl status postgresql
sudo systemctl status redis
```

### 2. Проверка логов
```bash
# Логи Django
tail -f /home/pasynkun/222_ru_fl/logs/django.log

# Логи Gunicorn
sudo journalctl -u filehost -f

# Логи Celery
sudo journalctl -u celery -f
sudo journalctl -u celerybeat -f

# Логи Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### 3. Тестирование производительности
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить тест производительности
python production_performance_test.py
```

## 🔧 Полезные команды

### Управление сервисами
```bash
# Перезапуск всех сервисов
sudo systemctl restart filehost celery celerybeat nginx

# Проверка статуса
sudo systemctl status filehost celery celerybeat nginx

# Просмотр логов
sudo journalctl -u filehost -n 50
sudo journalctl -u celery -n 50
```

### Управление базой данных
```bash
# Резервное копирование
pg_dump -U filehost_user -h localhost filehost > backup.sql

# Восстановление
psql -U filehost_user -h localhost filehost < backup.sql
```

### Обновление кода
```bash
# Получить обновления из Git
git pull origin master

# Применить миграции
python manage.py migrate --settings=filehost.settings_prod

# Пересобрать статические файлы
python manage.py collectstatic --settings=filehost.settings_prod --noinput

# Перезапустить сервисы
sudo systemctl restart filehost celery celerybeat
```

## 🆘 Устранение неполадок

### Если сервисы не запускаются:
```bash
# Проверить логи
sudo journalctl -u filehost -n 100
sudo journalctl -u celery -n 100

# Проверить права доступа
ls -la /home/pasynkun/222_ru_fl/
ls -la /var/log/gunicorn/
ls -la /var/log/celery/
```

### Если база данных недоступна:
```bash
# Проверить статус PostgreSQL
sudo systemctl status postgresql

# Проверить подключение
psql -U filehost_user -h localhost -d filehost
```

### Если Redis недоступен:
```bash
# Проверить статус Redis
sudo systemctl status redis

# Проверить подключение
redis-cli ping
```

## 📊 Мониторинг

### Проверка ресурсов
```bash
# Использование CPU и памяти
htop

# Использование диска
df -h

# Использование сети
iftop
```

### Проверка производительности
```bash
# Тест загрузки
ab -n 1000 -c 10 http://pasynkun.beget.tech/

# Тест через Python скрипт
python production_performance_test.py
```

## 🎉 Готово!

После выполнения всех шагов ваш файловый хостинг будет доступен по адресу:
**http://pasynkun.beget.tech/**

### Основные URL:
- Главная страница: `http://pasynkun.beget.tech/`
- Загрузка файлов: `http://pasynkun.beget.tech/`
- Просмотр файла: `http://pasynkun.beget.tech/file/{code}/`
- Скачивание файла: `http://pasynkun.beget.tech/download/{code}/`

### Статистика:
- Ожидаемая производительность: 200-500 одновременных пользователей
- Время отклика: 20-80ms для страниц, 100-300ms для загрузки файлов
- Поддержка файлов до 100MB

Удачи с развертыванием! 🚀
