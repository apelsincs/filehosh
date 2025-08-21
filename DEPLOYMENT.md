# 🚀 Развертывание 0123.ru на VPS

Подробное руководство по развертыванию файлового хостинга на VPS с Ubuntu/Debian.

## 📋 Требования к VPS

- **ОС:** Ubuntu 20.04+ или Debian 11+
- **RAM:** Минимум 2GB (рекомендуется 4GB+)
- **CPU:** 2 ядра (рекомендуется 4+)
- **Диск:** 20GB+ SSD
- **Сеть:** Статический IP адрес

## 🎯 Рекомендуемые провайдеры

- **Vultr** - от $5/месяц, отличная производительность
- **Linode** - от $5/месяц, надежность
- **DigitalOcean** - от $5/месяц, простота
- **Hetzner** - от €4/месяц, хорошее соотношение цена/качество

## 🚀 Быстрое развертывание

### 1. Подготовка VPS

```bash
# Подключитесь к VPS
ssh root@YOUR_SERVER_IP

# Обновите систему
apt update && apt upgrade -y

# Установите необходимые пакеты
apt install -y git curl wget
```

### 2. Клонирование проекта

```bash
# Клонируйте репозиторий
git clone https://github.com/apelsincs/filehosh.git
cd filehost

# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите автоматическое развертывание
./deploy.sh
```

## 🔧 Ручное развертывание

Если автоматический скрипт не подходит, выполните шаги вручную:

### 1. Установка зависимостей

```bash
# Системные пакеты
apt install -y python3 python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server nginx \
    libpq-dev build-essential libmagic1 \
    supervisor ufw fail2ban

# Python зависимости
cd /var/www/filehost
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt
```

### 2. Настройка базы данных

```bash
# Создание пользователя и базы
sudo -u postgres createuser --interactive --pwprompt www-data
sudo -u postgres createdb filehost

# Проверка подключения
sudo -u www-data psql -d filehost -c "\l"
```

### 3. Настройка Redis

```bash
# Redis уже установлен и запущен
systemctl status redis
systemctl enable redis
```

### 4. Конфигурация Django

```bash
# Копирование переменных окружения
cp env.production .env

# Генерация секретного ключа
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
sed -i "s/your-super-secret-key-here-change-this/$SECRET_KEY/" .env

# Обновление IP сервера
SERVER_IP=$(curl -s ifconfig.me)
sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" .env

# Миграции и статические файлы
python manage.py migrate --settings=filehost.settings_prod
python manage.py collectstatic --noinput --settings=filehost.settings_prod
```

### 5. Настройка Gunicorn

```bash
# Создание лог директорий
mkdir -p /var/log/gunicorn
chown www-data:www-data /var/log/gunicorn

# Копирование конфигурации
cp gunicorn.conf.py /var/www/filehost/
chown www-data:www-data /var/www/filehost/gunicorn.conf.py
```

### 6. Настройка systemd

```bash
# Копирование сервис файла
cp filehost.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable filehost
systemctl start filehost
```

### 7. Настройка Nginx

```bash
# Копирование конфигурации
cp nginx.conf /etc/nginx/sites-available/filehost
sed -i "s/YOUR_SERVER_IP/$SERVER_IP/g" /etc/nginx/sites-available/filehost

# Активация сайта
ln -sf /etc/nginx/sites-available/filehost /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
nginx -t
systemctl restart nginx
```

### 8. Настройка файрвола

```bash
# Настройка UFW
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# Проверка статуса
ufw status
```

## 🔒 Безопасность

### 1. Настройка fail2ban

```bash
# fail2ban уже установлен
systemctl enable fail2ban
systemctl start fail2ban

# Проверка статуса
fail2ban-client status
```

### 2. Обновление системы

```bash
# Автоматические обновления безопасности
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

### 3. Мониторинг логов

```bash
# Django логи
tail -f /var/www/filehost/logs/django.log

# Gunicorn логи
journalctl -u filehost -f

# Nginx логи
tail -f /var/log/nginx/filehost_access.log
tail -f /var/log/nginx/filehost_error.log
```

## 🌐 Настройка домена

Когда у вас появится домен:

### 1. Обновление DNS

```bash
# Добавьте A запись в DNS
# yourdomain.com -> YOUR_SERVER_IP
# www.yourdomain.com -> YOUR_SERVER_IP
```

### 2. Обновление .env файла

```bash
# Редактируйте .env файл
nano /var/www/filehost/.env

# Обновите параметры:
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,YOUR_SERVER_IP
SITE_BASE_URL=https://yourdomain.com
USE_HTTPS=True
```

### 3. Настройка SSL

```bash
# Установка Certbot
apt install certbot python3-certbot-nginx

# Получение сертификата
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Автоматическое обновление
crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Перезапуск сервисов

```bash
systemctl restart filehost
systemctl restart nginx
```

## 📊 Мониторинг и обслуживание

### 1. Проверка статуса сервисов

```bash
systemctl status filehost
systemctl status nginx
systemctl status postgresql
systemctl status redis
```

### 2. Обновление приложения

```bash
cd /var/www/filehost
git pull origin master
source venv/bin/activate
pip install -r requirements-prod.txt
python manage.py migrate --settings=filehost.settings_prod
python manage.py collectstatic --noinput --settings=filehost.settings_prod
systemctl restart filehost
```

### 3. Резервное копирование

```bash
# База данных
pg_dump filehost > backup_$(date +%Y%m%d_%H%M%S).sql

# Медиа файлы
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

## 🚨 Устранение неполадок

### 1. Проверка логов

```bash
# Django ошибки
tail -f /var/www/filehost/logs/django.log

# Gunicorn ошибки
journalctl -u filehost -f

# Nginx ошибки
tail -f /var/log/nginx/error.log
```

### 2. Проверка портов

```bash
# Проверка открытых портов
netstat -tlnp | grep :80
netstat -tlnp | grep :8000
netstat -tlnp | grep :5432
netstat -tlnp | grep :6379
```

### 3. Перезапуск сервисов

```bash
# Полный перезапуск
systemctl restart postgresql
systemctl restart redis
systemctl restart filehost
systemctl restart nginx
```

## 📞 Поддержка

Если возникли проблемы:

1. **Проверьте логи** (см. раздел "Устранение неполадок")
2. **Создайте issue** на GitHub: https://github.com/apelsincs/filehosh/issues
3. **Email:** support@0123.ru

---

**🎉 Поздравляем! Ваш файловый хостинг успешно развернут на VPS!**
