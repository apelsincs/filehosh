# 🚀 Руководство по развертыванию 0123.ru

Подробная инструкция по размещению файлового хостинга на различных платформах.

## 📋 Содержание

1. [Подготовка к развертыванию](#подготовка-к-развертыванию)
2. [VPS/Сервер](#vpsсервер)
3. [Heroku](#heroku)
4. [DigitalOcean App Platform](#digitalocean-app-platform)
5. [Railway](#railway)
6. [Render](#render)
7. [Vercel](#vercel)
8. [Docker](#docker)
9. [Мониторинг и поддержка](#мониторинг-и-поддержка)

## 🔧 Подготовка к развертыванию

### 1. Подготовка проекта

```bash
# Клонирование репозитория
git clone https://github.com/your-username/0123-ru-filehost.git
cd 0123-ru-filehost

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Заполните `.env` файл:

```bash
# Django настройки
SECRET_KEY=your-super-secret-key-here-change-this-immediately
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# База данных
DATABASE_URL=postgresql://username:password@localhost/database_name

# Безопасность
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# Настройки файлов
MAX_FILE_SIZE=26214400
FILE_EXPIRY_HOURS=24
QR_CODE_SIZE=10

# Rate limiting
RATE_LIMIT_UPLOAD=5
RATE_LIMIT_API=10
RATE_LIMIT_WINDOW=60

# Redis (для кеширования)
REDIS_URL=redis://localhost:6379/0
```

### 3. Генерация SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(50))
```

## 🖥️ VPS/Сервер

### Ubuntu/Debian

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server git curl

# Установка Node.js (для сборки статических файлов)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 2. Настройка PostgreSQL

```bash
# Создание пользователя и базы данных
sudo -u postgres createuser filehost_user
sudo -u postgres createdb filehost_db
sudo -u postgres psql -c "ALTER USER filehost_user PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE filehost_db TO filehost_user;"
```

#### 3. Настройка проекта

```bash
# Создание пользователя для приложения
sudo useradd -m -s /bin/bash filehost
sudo usermod -aG sudo filehost

# Переключение на пользователя
sudo su - filehost

# Клонирование проекта
git clone https://github.com/your-username/0123-ru-filehost.git
cd 0123-ru-filehost

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.example .env
nano .env  # Отредактируйте файл
```

#### 4. Настройка Django

```bash
# Миграции
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Сборка статических файлов
python manage.py collectstatic --noinput

# Создание директорий для логов
sudo mkdir -p /var/log/filehost
sudo chown filehost:filehost /var/log/filehost
```

#### 5. Настройка Gunicorn

Создайте файл `gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "filehost"
group = "filehost"
```

#### 6. Systemd сервис

Создайте `/etc/systemd/system/filehost.service`:

```ini
[Unit]
Description=0123.ru Filehost
After=network.target postgresql.service redis.service

[Service]
User=filehost
Group=filehost
WorkingDirectory=/home/filehost/0123-ru-filehost
Environment="PATH=/home/filehost/0123-ru-filehost/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=filehost.settings"
ExecStart=/home/filehost/0123-ru-filehost/venv/bin/gunicorn --config gunicorn.conf.py filehost.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 7. Настройка Nginx

Создайте `/etc/nginx/sites-available/filehost`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Редирект на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Статические файлы
    location /static/ {
        alias /home/filehost/0123-ru-filehost/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
    
    # Медиа файлы
    location /media/ {
        alias /home/filehost/0123-ru-filehost/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }
    
    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
```

#### 8. SSL сертификат (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

#### 9. Запуск сервисов

```bash
# Активация сайта
sudo ln -s /etc/nginx/sites-available/filehost /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Запуск сервисов
sudo systemctl enable filehost
sudo systemctl start filehost
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl enable redis
sudo systemctl start redis

# Проверка статуса
sudo systemctl status filehost nginx redis
```

## ☁️ Heroku

### 1. Подготовка

```bash
# Установка Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Логин в Heroku
heroku login

# Создание приложения
heroku create your-filehost-app
```

### 2. Настройка проекта

Создайте `Procfile`:

```
web: gunicorn filehost.wsgi:application --bind 0.0.0.0:$PORT
release: python manage.py migrate
```

Создайте `runtime.txt`:

```
python-3.13.0
```

### 3. Настройка переменных окружения

```bash
# Основные настройки
heroku config:set SECRET_KEY="your-secret-key"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app.herokuapp.com"

# База данных
heroku addons:create heroku-postgresql:mini

# Redis
heroku addons:create heroku-redis:mini

# Другие настройки
heroku config:set MAX_FILE_SIZE=26214400
heroku config:set FILE_EXPIRY_HOURS=24
heroku config:set RATE_LIMIT_UPLOAD=5
heroku config:set RATE_LIMIT_API=10
```

### 4. Деплой

```bash
# Добавление Heroku как remote
heroku git:remote -a your-filehost-app

# Деплой
git add .
git commit -m "Initial deployment"
git push heroku main

# Запуск миграций
heroku run python manage.py migrate

# Создание суперпользователя
heroku run python manage.py createsuperuser

# Сборка статических файлов
heroku run python manage.py collectstatic --noinput
```

## 🌊 DigitalOcean App Platform

### 1. Подготовка

Создайте `app.yaml`:

```yaml
name: filehost
services:
- name: web
  source_dir: /
  github:
    repo: your-username/0123-ru-filehost
    branch: main
  run_command: gunicorn filehost.wsgi:application --bind 0.0.0.0:$PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DEBUG
    value: "False"
  - key: ALLOWED_HOSTS
    value: your-app.ondigitalocean.app
  - key: MAX_FILE_SIZE
    value: "26214400"
  - key: FILE_EXPIRY_HOURS
    value: "24"

databases:
- name: db
  engine: PG
  version: "12"
  production: false

redis:
- name: redis
  version: "6"
  production: false
```

### 2. Деплой

```bash
# Установка doctl
snap install doctl

# Логин
doctl auth init

# Создание приложения
doctl apps create --spec app.yaml
```

## 🚂 Railway

### 1. Подготовка

Создайте `railway.json`:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn filehost.wsgi:application --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 2. Деплой

```bash
# Установка Railway CLI
npm install -g @railway/cli

# Логин
railway login

# Инициализация проекта
railway init

# Деплой
railway up
```

## 🎨 Render

### 1. Подготовка

Создайте `render.yaml`:

```yaml
services:
  - type: web
    name: filehost
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn filehost.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false
      - key: ALLOWED_HOSTS
        value: your-app.onrender.com
      - key: MAX_FILE_SIZE
        value: 26214400
      - key: FILE_EXPIRY_HOURS
        value: 24

databases:
  - name: filehost-db
    databaseName: filehost
    user: filehost
```

### 2. Деплой

1. Подключите GitHub репозиторий к Render
2. Создайте новый Web Service
3. Настройте переменные окружения
4. Деплой автоматически запустится

## ⚡ Vercel

### 1. Подготовка

Создайте `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "filehost/wsgi.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "filehost/wsgi.py"
    }
  ],
  "env": {
    "SECRET_KEY": "your-secret-key",
    "DEBUG": "False",
    "ALLOWED_HOSTS": "your-app.vercel.app"
  }
}
```

### 2. Деплой

```bash
# Установка Vercel CLI
npm install -g vercel

# Логин
vercel login

# Деплой
vercel --prod
```

## 🐳 Docker

### 1. Dockerfile

```dockerfile
FROM python:3.13-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание пользователя
RUN useradd -m -u 1000 filehost && chown -R filehost:filehost /app
USER filehost

# Сборка статических файлов
RUN python manage.py collectstatic --noinput

# Порт
EXPOSE 8000

# Команда запуска
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "filehost.wsgi:application"]
```

### 2. Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://filehost:password@db:5432/filehost
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=your-secret-key
      - DEBUG=False
      - ALLOWED_HOSTS=localhost,127.0.0.1
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=filehost
      - POSTGRES_USER=filehost
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/var/www/static
      - ./media:/var/www/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. Запуск

```bash
# Сборка и запуск
docker-compose up -d

# Миграции
docker-compose exec web python manage.py migrate

# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser
```

## 📊 Мониторинг и поддержка

### 1. Логирование

```bash
# Просмотр логов приложения
sudo journalctl -u filehost -f

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Просмотр логов Django
tail -f /var/log/filehost/django.log
```

### 2. Мониторинг производительности

```bash
# Установка зависимостей для тестирования
pip install aiohttp

# Запуск тестов производительности
python performance_test.py --url https://your-domain.com

# Генерация отчета
python performance_test.py --report performance_test_results_1234567890.json
```

### 3. Резервное копирование

```bash
# Скрипт резервного копирования
#!/bin/bash
BACKUP_DIR="/backups/filehost"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание директории
mkdir -p $BACKUP_DIR

# Резервное копирование базы данных
pg_dump filehost_db > $BACKUP_DIR/db_$DATE.sql

# Резервное копирование медиа файлов
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /home/filehost/0123-ru-filehost/media/

# Удаление старых резервных копий (старше 30 дней)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 4. Автоматическое обновление

```bash
# Скрипт обновления
#!/bin/bash
cd /home/filehost/0123-ru-filehost

# Остановка сервиса
sudo systemctl stop filehost

# Обновление кода
git pull origin main

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей
pip install -r requirements.txt

# Миграции
python manage.py migrate

# Сборка статических файлов
python manage.py collectstatic --noinput

# Запуск сервиса
sudo systemctl start filehost

# Проверка статуса
sudo systemctl status filehost
```

## 🔧 Устранение неполадок

### Частые проблемы

1. **Ошибка 502 Bad Gateway**
   - Проверьте статус Gunicorn: `sudo systemctl status filehost`
   - Проверьте логи: `sudo journalctl -u filehost -f`

2. **Ошибка подключения к базе данных**
   - Проверьте настройки DATABASE_URL
   - Убедитесь, что PostgreSQL запущен

3. **Статические файлы не загружаются**
   - Выполните `python manage.py collectstatic`
   - Проверьте права доступа к папке staticfiles

4. **Медленная работа**
   - Проверьте настройки Redis
   - Оптимизируйте базу данных
   - Увеличьте количество воркеров Gunicorn

### Полезные команды

```bash
# Проверка статуса всех сервисов
sudo systemctl status filehost nginx postgresql redis

# Перезапуск сервисов
sudo systemctl restart filehost nginx

# Проверка конфигурации Nginx
sudo nginx -t

# Просмотр использования ресурсов
htop
df -h
free -h

# Проверка портов
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443
sudo netstat -tlnp | grep :8000
```

## 📞 Поддержка

- **Документация**: [GitHub Wiki](https://github.com/your-username/0123-ru-filehost/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/0123-ru-filehost/issues)
- **Email**: support@0123.ru

---

**Удачного развертывания! 🚀**
