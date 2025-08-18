# 0123.ru - Файловый хостинг

Современный файловый хостинг с анонимными сессиями, защитой паролем и автоматическим удалением файлов.

## 🚀 Возможности

### Основной функционал
- **Загрузка файлов** до 25 МБ с автоматической генерацией кодов
- **Кастомные коды** - пользователи могут задавать свои коды для файлов
- **Защита паролем** - файлы можно защитить паролем любой сложности
- **QR-коды** - автоматическая генерация QR-кодов для быстрого доступа
- **Анонимные сессии** - файлы привязаны к сессии без регистрации
- **Автоматическое удаление** - файлы удаляются через 24 часа

### UI/UX
- **Современный UI** - интуитивный интерфейс с анимациями
- **Темная/светлая тема** - переключение между темами
- **Адаптивный дизайн** - работает на всех устройствах
- **Валидация в реальном времени** - проверка доступности кодов

### Безопасность
- **Rate limiting** - защита от DDoS атак
- **CSRF защита** - защита от межсайтовых запросов
- **Валидация файлов** - проверка типов и размеров
- **Безопасные хеши** - пароли хранятся в хешированном виде
- **Мониторинг безопасности** - логирование подозрительной активности

## 🛠 Технологии

- **Backend**: Django 5.2.4, Python 3.13
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **База данных**: SQLite (для разработки), PostgreSQL/MySQL (для продакшена)
- **Стили**: Современный UI, Bootstrap 5
- **Иконки**: Font Awesome
- **QR-коды**: qrcode library
- **Безопасность**: django-ratelimit, django-crispy-forms

## 📦 Установка и развертывание

### Локальная разработка

1. **Клонирование репозитория**
```bash
git clone https://github.com/your-username/0123-ru-filehost.git
cd 0123-ru-filehost
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка переменных окружения**
```bash
cp env.example .env
# Отредактируйте .env файл
```

5. **Миграции базы данных**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Создание суперпользователя (опционально)**
```bash
python manage.py createsuperuser
```

7. **Запуск сервера разработки**
```bash
python manage.py runserver
```

### Продакшен развертывание

#### Вариант 1: VPS/Сервер

1. **Подготовка сервера**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# Установка Redis (для кеширования)
sudo apt install redis-server
```

2. **Настройка PostgreSQL**
```bash
sudo -u postgres createuser filehost_user
sudo -u postgres createdb filehost_db
sudo -u postgres psql -c "ALTER USER filehost_user PASSWORD 'your_password';"
```

3. **Настройка проекта**
```bash
# Клонирование и настройка
git clone https://github.com/your-username/0123-ru-filehost.git
cd 0123-ru-filehost

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Переменные окружения
cp env.example .env
nano .env  # Настройте переменные
```

4. **Настройка Django для продакшена**
```python
# В settings.py
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'filehost_db',
        'USER': 'filehost_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Статические файлы
STATIC_ROOT = '/var/www/filehost/static/'
MEDIA_ROOT = '/var/www/filehost/media/'
```

5. **Настройка Gunicorn**
```bash
pip install gunicorn
```

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
```

6. **Настройка Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location /static/ {
        alias /var/www/filehost/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/filehost/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

7. **Systemd сервис**
Создайте `/etc/systemd/system/filehost.service`:
```ini
[Unit]
Description=0123.ru Filehost
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/filehost
Environment="PATH=/var/www/filehost/venv/bin"
ExecStart=/var/www/filehost/venv/bin/gunicorn --config gunicorn.conf.py filehost.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

8. **Запуск сервисов**
```bash
sudo systemctl enable filehost
sudo systemctl start filehost
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### Вариант 2: Docker

1. **Создание Dockerfile**
```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "filehost.wsgi:application"]
```

2. **Docker Compose**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/filehost
    depends_on:
      - db
    volumes:
      - ./media:/app/media
      - ./staticfiles:/app/staticfiles

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=filehost
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔧 Конфигурация

### Переменные окружения (.env)

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/filehost

# Файлы
MAX_FILE_SIZE=26214400  # 25 МБ в байтах
FILE_EXPIRY_HOURS=24

# Безопасность
RATE_LIMIT_UPLOAD=5
RATE_LIMIT_API=10
RATE_LIMIT_WINDOW=60

# Redis (для кеширования)
REDIS_URL=redis://localhost:6379/0
```

### Настройки производительности

```python
# settings.py

# Кеширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Сессии
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/filehost/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 📊 Производительность

### Тестирование нагрузки

Проект может обрабатывать:
- **1000+ одновременных пользователей** с правильной настройкой
- **100+ загрузок в минуту** с rate limiting
- **Файлы до 25 МБ** с оптимизированной обработкой

### Оптимизация

1. **База данных**
   - Индексы на часто используемых полях
   - Партиционирование по дате для больших таблиц
   - Connection pooling

2. **Кеширование**
   - Redis для сессий и кеша
   - CDN для статических файлов
   - Browser caching

3. **Файловая система**
   - SSD диски для быстрого доступа
   - Оптимизированная структура папок
   - Автоматическая очистка

## 🔒 Безопасность

### Реализованные меры
- CSRF защита
- Rate limiting
- Валидация файлов
- Безопасные хеши паролей
- Логирование безопасности
- Защита от XSS и SQL инъекций

### Рекомендации
- Использование HTTPS
- Регулярные обновления зависимостей
- Мониторинг логов безопасности
- Резервное копирование данных

## 🚀 Автоматизация

### Cron задачи
```bash
# Добавление задачи очистки
python manage.py crontab add

# Просмотр активных задач
python manage.py crontab show

# Удаление задач
python manage.py crontab remove
```

### Ручная очистка
```bash
# Просмотр файлов для удаления
python manage.py cleanup_expired_files --dry-run

# Удаление истекших файлов
python manage.py cleanup_expired_files
```

## 📝 API

### Основные эндпоинты
- `GET /` - Главная страница
- `POST /` - Загрузка файла
- `GET /<code>/` - Просмотр файла
- `GET /<code>/download/` - Скачивание файла
- `GET /recent/` - Недавние файлы
- `GET /check-code/` - Проверка доступности кода

### Форматы ответов
```json
{
    "success": true,
    "code": "ABC123",
    "url": "https://domain.com/ABC123/",
    "download_url": "https://domain.com/ABC123/download/",
    "qr_url": "https://domain.com/media/qr_codes/qr_ABC123.png",
    "expires_at": "2025-08-15T06:58:08.665310+00:00",
    "file_size": 65393,
    "filename": "example.jpg",
    "is_protected": false
}
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 📞 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-username/0123-ru-filehost/issues)
- **Email**: support@0123.ru
- **Документация**: [Wiki](https://github.com/your-username/0123-ru-filehost/wiki)

---

**0123.ru** - Быстрый и безопасный файловый хостинг для всех! 🚀
