# 📁 0123.ru - Быстрый файловый хостинг

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://0123.ru)

Современный файловый хостинг для быстрой передачи файлов без регистрации. Автоматическое удаление через 24 часа, защита паролем, QR-коды и адаптивный дизайн.

## ✨ Особенности

- 🚀 **Мгновенная загрузка** файлов до 25MB
- 🔒 **Защита паролем** для конфиденциальных файлов
- 📱 **QR-коды** для быстрого доступа с мобильных устройств
- 🎨 **Адаптивный дизайн** с поддержкой светлой и темной темы
- 🔄 **Автоматическое удаление** файлов через 24 часа
- 👤 **Анонимные сессии** без необходимости регистрации
- 📊 **Детальная статистика** загрузок и просмотров
- 🎯 **Умные иконки** для разных типов файлов

## 🛠 Технологии

- **Backend:** Django 5.2+, Python 3.8+
- **Frontend:** Bootstrap 5, Font Awesome, CSS Grid/Flexbox
- **Database:** SQLite (разработка) / PostgreSQL (продакшн)
- **Security:** CSRF защита, rate limiting, безопасные заголовки
- **Deployment:** WSGI/ASGI серверы, Docker-ready

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- pip
- virtualenv (рекомендуется)

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/apelsincs/filehosh.git
cd filehosh
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp env.example .env
# Отредактируйте .env файл
```

5. **Выполните миграции:**
```bash
python manage.py migrate
```

6. **Создайте суперпользователя (опционально):**
```bash
python manage.py createsuperuser
```

7. **Запустите сервер:**
```bash
python manage.py runserver
```

Откройте [http://localhost:8000](http://localhost:8000) в браузере!

## 📁 Структура проекта

```
filehosh/
├── filehost/          # Основные настройки Django
├── files/             # Приложение для работы с файлами
│   ├── models.py      # Модели данных
│   ├── views.py       # Представления
│   ├── urls.py        # URL маршруты
│   └── templates/     # HTML шаблоны
├── static/            # Статические файлы (CSS, JS, изображения)
├── media/             # Загруженные файлы
├── templates/         # Базовые шаблоны
└── manage.py          # Django CLI
```

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` на основе `env.example`:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,0123.ru
SITE_BASE_URL=http://localhost:8000
FILE_EXPIRY_HOURS=24
MAX_FILE_SIZE=26214400
```

### Настройки безопасности

- **CSRF защита** включена по умолчанию
- **Rate limiting** для предотвращения спама
- **Безопасные заголовки** HTTP
- **Валидация файлов** по типу и размеру

## 📱 Использование

### Загрузка файла

1. Перетащите файл в область загрузки или нажмите для выбора
2. При необходимости установите пароль для защиты
3. Нажмите "Загрузить файл"
4. Получите уникальный код для доступа к файлу

### Доступ к файлу

- **Прямая ссылка:** `https://0123.ru/files/КОД_ФАЙЛА/`
- **QR-код:** отсканируйте для мобильного доступа
- **Скачивание:** `https://0123.ru/files/КОД_ФАЙЛА/download/`

### Типы файлов

Система автоматически определяет тип файла и показывает соответствующую иконку:

- 📷 **Изображения:** JPG, PNG, GIF, WebP, SVG
- 🎥 **Видео:** MP4, AVI, MOV, WebM, MKV
- 🎵 **Аудио:** MP3, WAV, FLAC, AAC, OGG
- 📄 **Документы:** PDF, DOC, TXT, RTF, ODT
- 📊 **Таблицы:** XLS, XLSX, CSV, ODS
- 🎯 **Презентации:** PPT, PPTX, ODP
- 📦 **Архивы:** ZIP, RAR, 7Z, TAR, GZ
- 💻 **Код:** PY, JS, HTML, CSS, PHP, Java, C++
- ⚙️ **Программы:** EXE, MSI, DMG, PKG, DEB, RPM

## 🎨 Темы оформления

- **Светлая тема** - классический дизайн
- **Темная тема** - современный темный интерфейс
- **Автоматическое переключение** по системным настройкам
- **Плавные переходы** между темами

## 🔒 Безопасность

- **Автоматическое удаление** файлов через 24 часа
- **Защита паролем** для конфиденциальных файлов
- **Rate limiting** для предотвращения злоупотреблений
- **Валидация типов файлов** для безопасности
- **Анонимные сессии** без хранения персональных данных

## 📊 API

### Загрузка файла

```http
POST / HTTP/1.1
Content-Type: multipart/form-data

file: [binary data]
is_protected: false
password: [optional]
custom_code: [optional]
```

### Ответ

```json
{
  "success": true,
  "code": "ABC123",
  "url": "https://0123.ru/files/ABC123/",
  "download_url": "https://0123.ru/files/ABC123/download/",
  "file_type": "document",
  "file_type_name": "Документ",
  "file_type_icon": "fas fa-file-alt"
}
```

## 🚀 Развертывание

### Docker (рекомендуется)

```bash
docker-compose up -d
```

### Ручное развертывание

1. **Настройте веб-сервер** (Nginx/Apache)
2. **Настройте WSGI сервер** (Gunicorn/uWSGI)
3. **Настройте базу данных** (PostgreSQL для продакшна)
4. **Настройте статические файлы** и медиа
5. **Настройте SSL сертификат**

### Переменные продакшна

```env
DEBUG=False
ALLOWED_HOSTS=0123.ru,www.0123.ru
DATABASE_URL=postgresql://user:pass@localhost/filehosh
SITE_BASE_URL=https://0123.ru
```

## 🤝 Разработка

### Установка для разработки

```bash
git clone https://github.com/apelsincs/filehosh.git
cd filehosh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # дополнительные инструменты разработки
```

### Запуск тестов

```bash
python manage.py test
python manage.py test --coverage
```

### Линтинг и форматирование

```bash
flake8 files/
black files/
isort files/
```

## 📝 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## 🙏 Благодарности

- [Django](https://djangoproject.com) - веб-фреймворк
- [Bootstrap](https://getbootstrap.com) - CSS фреймворк
- [Font Awesome](https://fontawesome.com) - иконки
- [QR Code](https://github.com/lincolnloop/python-qrcode) - генерация QR кодов

## 📞 Поддержка

- **Веб-сайт:** [https://0123.ru](https://0123.ru)
- **GitHub Issues:** [https://github.com/apelsincs/filehosh/issues](https://github.com/apelsincs/filehosh/issues)
- **Email:** support@0123.ru

---

**⭐ Если проект вам понравился, поставьте звездочку на GitHub!**
