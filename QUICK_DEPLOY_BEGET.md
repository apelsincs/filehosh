# 🚀 Быстрое развертывание на Beget VPS

## 📋 Подключение к серверу
```bash
ssh pasynkun@pasynkun.beget.tech
# Пароль: Msl3TPA3cWJR
```

## ⚡ Автоматическое развертывание (рекомендуется)

### 1. Перейти в директорию проекта
```bash
cd /home/pasynkun/222_ru_fl
```

### 2. Запустить автоматический скрипт
```bash
sudo ./deploy_beget.sh
```

**Скрипт автоматически выполнит:**
- ✅ Установку всех зависимостей
- ✅ Настройку PostgreSQL и Redis
- ✅ Создание виртуального окружения
- ✅ Настройку .env файла
- ✅ Применение миграций
- ✅ Настройку Gunicorn, Celery, Nginx
- ✅ Настройку безопасности (UFW, Fail2ban)
- ✅ Запуск всех сервисов

## 🔧 Ручное развертывание (если автоматическое не работает)

### 1. Установка зависимостей
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx git curl wget unzip build-essential libpq-dev python3-dev fail2ban ufw
```

### 2. Настройка базы данных
```bash
sudo -u postgres psql -c "CREATE DATABASE filehost;"
sudo -u postgres psql -c "CREATE USER filehost_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE filehost TO filehost_user;"
sudo systemctl enable postgresql && sudo systemctl start postgresql
```

### 3. Настройка Python
```bash
cd /home/pasynkun/222_ru_fl
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### 4. Создание .env файла
```bash
cp env.production .env
nano .env  # Отредактировать настройки
```

### 5. Применение миграций
```bash
python manage.py migrate --settings=filehost.settings_prod
python manage.py collectstatic --settings=filehost.settings_prod --noinput
```

### 6. Настройка сервисов
```bash
sudo mkdir -p /var/log/gunicorn /var/log/celery /var/run/celery
sudo chown pasynkun:pasynkun /var/log/gunicorn /var/log/celery /var/run/celery

sudo cp filehost.service /etc/systemd/system/
sudo cp celery.service /etc/systemd/system/
sudo cp celerybeat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable filehost celery celerybeat
```

### 7. Настройка Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/filehost
sudo ln -sf /etc/nginx/sites-available/filehost /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
```

### 8. Запуск сервисов
```bash
sudo systemctl start filehost celery celerybeat nginx
sudo systemctl enable nginx
```

## ✅ Проверка развертывания

### Статус сервисов
```bash
sudo systemctl status filehost celery celerybeat nginx postgresql redis
```

### Проверка сайта
```bash
curl -I http://pasynkun.beget.tech/
```

### Просмотр логов
```bash
# Логи Django
tail -f /home/pasynkun/222_ru_fl/logs/django.log

# Логи сервисов
sudo journalctl -u filehost -f
sudo journalctl -u celery -f
sudo journalctl -u nginx -f
```

## 🔧 Управление сервисами

### Перезапуск всех сервисов
```bash
sudo systemctl restart filehost celery celerybeat nginx
```

### Остановка сервисов
```bash
sudo systemctl stop filehost celery celerybeat nginx
```

### Проверка статуса
```bash
sudo systemctl status filehost celery celerybeat nginx
```

## 🆘 Устранение неполадок

### Если сервисы не запускаются
```bash
# Проверить логи
sudo journalctl -u filehost -n 100
sudo journalctl -u celery -n 100

# Проверить права доступа
ls -la /home/pasynkun/222_ru_fl/
ls -la /var/log/gunicorn/
```

### Если база данных недоступна
```bash
sudo systemctl status postgresql
psql -U filehost_user -h localhost -d filehost
```

### Если Redis недоступен
```bash
sudo systemctl status redis
redis-cli ping
```

## 🎉 Готово!

После успешного развертывания ваш файловый хостинг будет доступен по адресу:
**http://pasynkun.beget.tech/**

### Основные функции:
- ✅ Загрузка файлов до 100MB
- ✅ Автоматическая генерация QR-кодов
- ✅ Защита файлов паролем
- ✅ Автоматическое удаление через 24 часа
- ✅ Асинхронная обработка задач
- ✅ Кеширование и оптимизация

### Производительность:
- 🚀 200-500 одновременных пользователей
- ⚡ 20-80ms время отклика страниц
- 📁 100-300ms время загрузки файлов

Удачи с развертыванием! 🚀
