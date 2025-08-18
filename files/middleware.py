"""
Middleware для rate limiting и мониторинга безопасности
Защищает от DDoS атак и отслеживает подозрительную активность
"""

import logging
import secrets
import hashlib
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from django_ratelimit.exceptions import Ratelimited

# Настройка логирования для безопасности
security_logger = logging.getLogger('security')


class SecurityMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware для мониторинга безопасности и логирования подозрительной активности.
    """
    
    def process_request(self, request):
        """Логируем подозрительные запросы"""
        # Логируем попытки доступа к защищенным файлам
        if 'download' in request.path and request.method == 'GET':
            security_logger.info(f"Download attempt: {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        # Логируем загрузки файлов
        if request.method == 'POST' and request.FILES:
            security_logger.info(f"File upload: {request.path} from {request.META.get('REMOTE_ADDR')}")
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Дополнительный middleware для rate limiting (дублирует функционал декораторов).
    """
    
    def process_request(self, request):
        # Основной rate limiting уже реализован через декораторы
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления заголовков безопасности.
    """
    
    def process_response(self, request, response):
        """Добавляем заголовки безопасности к ответу"""
        # Запрещаем встраивание в iframe (защита от clickjacking)
        response['X-Frame-Options'] = 'DENY'
        
        # Запрещаем MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Включаем XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class AnonymousSessionMiddleware(MiddlewareMixin):
    """
    Middleware для управления анонимными сессиями пользователей.
    
    Генерирует уникальный session_id для каждого нового посетителя и сохраняет его в cookies.
    Этот ID используется для связывания загруженных файлов с конкретным пользователем
    без необходимости регистрации или авторизации.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cookie_name = 'anonymous_session_id'
        self.cookie_max_age = 365 * 24 * 60 * 60  # 1 год в секундах
    
    def process_request(self, request):
        """
        Обрабатываем каждый запрос и генерируем session_id если его нет.
        """
        # Получаем session_id из cookies
        session_id = request.COOKIES.get(self.cookie_name)
        
        if not session_id:
            # Генерируем новый уникальный session_id
            session_id = self._generate_session_id()
            # Сохраняем в request для использования в views
            request.anonymous_session_id = session_id
            # Устанавливаем флаг для установки cookie в ответе
            request.set_anonymous_cookie = True
        else:
            # Проверяем валидность существующего session_id
            if self._is_valid_session_id(session_id):
                request.anonymous_session_id = session_id
                request.set_anonymous_cookie = False
            else:
                # Если session_id невалидный, генерируем новый
                session_id = self._generate_session_id()
                request.anonymous_session_id = session_id
                request.set_anonymous_cookie = True
        
        return None
    
    def process_response(self, request, response):
        """
        Устанавливаем cookie с session_id если это новый пользователь.
        """
        if hasattr(request, 'set_anonymous_cookie') and request.set_anonymous_cookie:
            response.set_cookie(
                self.cookie_name,
                request.anonymous_session_id,
                max_age=self.cookie_max_age,
                httponly=True,  # Защита от XSS
                secure=not settings.DEBUG,  # HTTPS только в продакшене
                samesite='Lax'  # Защита от CSRF
            )
        
        return response
    
    def _generate_session_id(self):
        """
        Генерирует уникальный session_id на основе случайных данных.
        
        Returns:
            str: Уникальный 64-символьный идентификатор сессии
        """
        # Генерируем случайные данные
        random_data = secrets.token_bytes(32)
        # Создаем хеш для получения фиксированной длины
        session_id = hashlib.sha256(random_data).hexdigest()
        return session_id
    
    def _is_valid_session_id(self, session_id):
        """
        Проверяет валидность session_id.
        
        Args:
            session_id (str): ID сессии для проверки
            
        Returns:
            bool: True если session_id валидный, False иначе
        """
        # Проверяем длину (64 символа для SHA-256)
        if len(session_id) != 64:
            return False
        
        # Проверяем что это hex строка
        try:
            int(session_id, 16)
            return True
        except ValueError:
            return False
