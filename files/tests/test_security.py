"""
Тесты безопасности и rate limiting
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
import tempfile
import os

from ..models import File


class SecurityTestCase(TestCase):
    """Тесты безопасности"""
    
    def setUp(self):
        self.client = Client()
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.test_file.write(b'test content')
        self.test_file.close()
        
        # Создаем тестовый файл в базе
        self.file_instance = File.objects.create(
            file=self.test_file.name,
            filename='test.txt',
            file_size=len(b'test content'),
            code='TEST123',
            expires_at=timezone.now() + timedelta(hours=24)
        )
    
    def tearDown(self):
        # Очищаем тестовый файл
        if os.path.exists(self.test_file.name):
            os.unlink(self.test_file.name)
        
        # Очищаем кэш
        cache.clear()
    
    def test_csrf_protection(self):
        """Тест CSRF защиты"""
        # Отправляем POST без CSRF токена
        response = self.client.post(reverse('files:home'))
        self.assertEqual(response.status_code, 403)
    
    def test_rate_limiting_upload(self):
        """Тест rate limiting для загрузки файлов"""
        # Создаем тестовый файл для загрузки
        test_file = tempfile.NamedTemporaryFile(delete=False)
        test_file.write(b'test content')
        test_file.close()
        
        try:
            # Пытаемся загрузить файл 6 раз (превышаем лимит в 5)
            for i in range(6):
                with open(test_file.name, 'rb') as f:
                    response = self.client.post(reverse('files:home'), {
                        'file': f,
                        'custom_code': f'TEST{i}',
                    })
                    
                    if i < 5:
                        # Первые 5 запросов должны пройти
                        self.assertNotEqual(response.status_code, 429)
                    else:
                        # 6-й запрос должен быть заблокирован
                        self.assertEqual(response.status_code, 429)
        finally:
            os.unlink(test_file.name)
    
    def test_rate_limiting_download(self):
        """Тест rate limiting для скачивания файлов"""
        # Пытаемся скачать файл 21 раз (превышаем лимит в 20)
        for i in range(21):
            response = self.client.get(
                reverse('files:download_file', kwargs={'code': 'TEST123'})
            )
            
            if i < 20:
                # Первые 20 запросов должны пройти
                self.assertNotEqual(response.status_code, 429)
            else:
                # 21-й запрос должен быть заблокирован
                self.assertEqual(response.status_code, 429)
    
    def test_suspicious_request_detection(self):
        """Тест обнаружения подозрительных запросов"""
        # Подозрительные пути
        suspicious_paths = [
            '/admin/',
            '/wp-admin/',
            '/phpmyadmin/',
            '/?q=union select',
            '/?q=script>alert(1)</script>',
        ]
        
        for path in suspicious_paths:
            response = self.client.get(path)
            # Запрос должен быть обработан, но залогирован
            self.assertNotEqual(response.status_code, 500)
    
    def test_security_headers(self):
        """Тест security headers"""
        response = self.client.get(reverse('files:home'))
        
        # Проверяем наличие security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('X-XSS-Protection', response)
        
        # Проверяем значения
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
    
    def test_file_upload_validation(self):
        """Тест валидации загружаемых файлов"""
        # Создаем файл превышающий лимит
        large_file = tempfile.NamedTemporaryFile(delete=False)
        large_file.write(b'x' * (25 * 1024 * 1024 + 1))  # 25MB + 1 байт
        large_file.close()
        
        try:
            with open(large_file.name, 'rb') as f:
                response = self.client.post(reverse('files:home'), {
                    'file': f,
                })
                
                # Должна быть ошибка валидации
                self.assertNotEqual(response.status_code, 200)
        finally:
            os.unlink(large_file.name)
    
    def test_password_protection(self):
        """Тест защиты паролем"""
        # Создаем защищенный файл
        protected_file = File.objects.create(
            file=self.test_file.name,
            filename='protected.txt',
            file_size=len(b'test content'),
            code='PROTECT',
            password=make_password('secret123'),
            is_protected=True,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        # Попытка доступа без пароля
        response = self.client.get(
            reverse('files:file_detail', kwargs={'code': 'PROTECT'})
        )
        self.assertEqual(response.status_code, 200)  # Показываем форму пароля
        
        # Попытка доступа с неверным паролем
        response = self.client.post(
            reverse('files:file_detail', kwargs={'code': 'PROTECT'}),
            {'password': 'wrong_password'}
        )
        self.assertEqual(response.status_code, 200)  # Остаемся на форме
        
        # Доступ с верным паролем
        response = self.client.post(
            reverse('files:file_detail', kwargs={'code': 'PROTECT'}),
            {'password': 'secret123'}
        )
        self.assertEqual(response.status_code, 200)  # Успешный доступ


class RateLimitTestCase(TestCase):
    """Тесты rate limiting"""
    
    def setUp(self):
        self.client = Client()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @override_settings(RATE_LIMIT_UPLOAD=3, RATE_LIMIT_WINDOW=60)
    def test_custom_rate_limits(self):
        """Тест кастомных настроек rate limiting"""
        # Создаем тестовый файл
        test_file = tempfile.NamedTemporaryFile(delete=False)
        test_file.write(b'test content')
        test_file.close()
        
        try:
            # Пытаемся загрузить файл 4 раза (превышаем лимит в 3)
            for i in range(4):
                with open(test_file.name, 'rb') as f:
                    response = self.client.post(reverse('files:home'), {
                        'file': f,
                        'custom_code': f'CUSTOM{i}',
                    })
                    
                    if i < 3:
                        # Первые 3 запроса должны пройти
                        self.assertNotEqual(response.status_code, 429)
                    else:
                        # 4-й запрос должен быть заблокирован
                        self.assertEqual(response.status_code, 429)
        finally:
            os.unlink(test_file.name)
    
    def test_rate_limit_reset(self):
        """Тест сброса rate limit после истечения времени"""
        # Создаем тестовый файл
        test_file = tempfile.NamedTemporaryFile(delete=False)
        test_file.write(b'test content')
        test_file.close()
        
        try:
            # Загружаем файл 5 раз (до лимита)
            for i in range(5):
                with open(test_file.name, 'rb') as f:
                    response = self.client.post(reverse('files:home'), {
                        'file': f,
                        'custom_code': f'RESET{i}',
                    })
                    self.assertNotEqual(response.status_code, 429)
            
            # 6-й запрос должен быть заблокирован
            with open(test_file.name, 'rb') as f:
                response = self.client.post(reverse('files:home'), {
                    'file': f,
                    'custom_code': 'RESET6',
                })
                self.assertEqual(response.status_code, 429)
            
            # Очищаем rate limits
            cache.clear()
            
            # Теперь должен пройти
            with open(test_file.name, 'rb') as f:
                response = self.client.post(reverse('files:home'), {
                    'file': f,
                    'custom_code': 'RESET7',
                })
                self.assertNotEqual(response.status_code, 429)
        finally:
            os.unlink(test_file.name)
