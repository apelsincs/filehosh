# 🤝 Руководство для контрибьюторов

Спасибо за интерес к проекту 0123.ru! Мы приветствуем любой вклад в развитие файлового хостинга.

## 📋 Как внести свой вклад

### 1. Подготовка окружения

```bash
# Форк репозитория
# Клонирование вашего форка
git clone https://github.com/your-username/0123-ru-filehost.git
cd 0123-ru-filehost

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env.example .env
# Отредактируйте .env файл

# Миграции
python manage.py makemigrations
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser
```

### 2. Создание ветки

```bash
# Создание новой ветки для вашей функции
git checkout -b feature/your-feature-name

# Или для исправления бага
git checkout -b fix/your-bug-fix
```

### 3. Разработка

- Следуйте стилю кода проекта
- Добавляйте комментарии к сложным участкам кода
- Пишите тесты для новой функциональности
- Обновляйте документацию при необходимости

### 4. Коммиты

```bash
# Добавление изменений
git add .

# Создание коммита с описательным сообщением
git commit -m "feat: add new file upload feature"
git commit -m "fix: resolve password validation issue"
git commit -m "docs: update deployment guide"
```

### 5. Push и Pull Request

```bash
# Отправка изменений
git push origin feature/your-feature-name

# Создание Pull Request на GitHub
```

## 📝 Стиль кода

### Python

- Следуйте PEP 8
- Используйте type hints
- Добавляйте docstrings для функций и классов
- Максимальная длина строки: 88 символов

### JavaScript

- Используйте ES6+ синтаксис
- Следуйте Airbnb JavaScript Style Guide
- Добавляйте JSDoc комментарии

### HTML/CSS

- Используйте семантическую разметку
- Следуйте BEM методологии для CSS
- Обеспечивайте доступность (accessibility)

## 🧪 Тестирование

### Запуск тестов

```bash
# Установка зависимостей для тестирования
pip install pytest pytest-django

# Запуск тестов
python manage.py test

# Запуск с покрытием
coverage run --source='.' manage.py test
coverage report
```

### Написание тестов

```python
# Пример теста для views.py
from django.test import TestCase, Client
from django.urls import reverse

class FileUploadTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_file_upload(self):
        with open('test_file.txt', 'w') as f:
            f.write('test content')
            
        with open('test_file.txt', 'rb') as f:
            response = self.client.post(reverse('home'), {
                'file': f
            })
            
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
```

## 📚 Документация

### Обновление README

- Обновляйте README.md при добавлении новых функций
- Добавляйте примеры использования
- Обновляйте список зависимостей

### Документирование кода

```python
def upload_file(file, custom_code=None, password=None):
    """
    Загружает файл на сервер.
    
    Args:
        file: Загружаемый файл
        custom_code (str, optional): Пользовательский код файла
        password (str, optional): Пароль для защиты файла
        
    Returns:
        dict: Результат загрузки с URL и метаданными
        
    Raises:
        ValidationError: При ошибке валидации файла
    """
    pass
```

## 🐛 Сообщение о багах

### Создание Issue

При создании issue укажите:

1. **Краткое описание** проблемы
2. **Шаги для воспроизведения**
3. **Ожидаемое поведение**
4. **Фактическое поведение**
5. **Скриншоты** (если применимо)
6. **Информация о системе**:
   - ОС
   - Версия Python
   - Версия Django
   - Браузер (для frontend багов)

### Пример хорошего issue

```
**Описание**
При загрузке файла больше 25MB не отображается ошибка валидации.

**Шаги для воспроизведения**
1. Откройте главную страницу
2. Выберите файл размером 30MB
3. Нажмите "Загрузить"

**Ожидаемое поведение**
Должна появиться ошибка "Файл слишком большой"

**Фактическое поведение**
Страница зависает, ошибка не отображается

**Система**
- OS: Ubuntu 22.04
- Python: 3.13.0
- Django: 5.2.4
- Браузер: Chrome 120.0
```

## ✨ Предложение новых функций

### Создание Feature Request

1. **Описание функции** - что должно делать
2. **Обоснование** - зачем это нужно
3. **Предлагаемая реализация** (если есть идеи)
4. **Альтернативы** - что уже существует

### Пример Feature Request

```
**Описание**
Добавить поддержку загрузки нескольких файлов одновременно.

**Обоснование**
Пользователи часто хотят загрузить несколько файлов сразу, 
что сейчас требует множественных запросов.

**Предлагаемая реализация**
- Drag & drop для множественных файлов
- Progress bar для каждого файла
- Batch processing на сервере

**Альтернативы**
- Можно использовать zip архивы, но это менее удобно
```

## 🔄 Процесс ревью

### Pull Request

1. **Описание изменений** - что было изменено и зачем
2. **Тестирование** - как протестировать изменения
3. **Скриншоты** - для UI изменений
4. **Чеклист** - что было проверено

### Ревью кода

- Будьте вежливы и конструктивны
- Фокусируйтесь на коде, а не на человеке
- Предлагайте конкретные улучшения
- Отмечайте хорошие решения

## 🏷️ Типы коммитов

- `feat:` - новая функция
- `fix:` - исправление бага
- `docs:` - изменения в документации
- `style:` - форматирование кода
- `refactor:` - рефакторинг
- `test:` - добавление тестов
- `chore:` - обновление зависимостей, конфигурации

## 📞 Связь

- **Issues**: [GitHub Issues](https://github.com/your-username/0123-ru-filehost/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/0123-ru-filehost/discussions)
- **Email**: contributors@0123.ru

## 🎉 Благодарности

Все контрибьюторы будут добавлены в файл [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

**Спасибо за ваш вклад в развитие 0123.ru! 🚀**
