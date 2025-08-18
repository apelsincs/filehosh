"""
Команда для мониторинга безопасности
Анализирует логи безопасности и выявляет подозрительную активность
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict


class Command(BaseCommand):
    help = 'Мониторинг безопасности и анализ подозрительной активности'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-logs',
            action='store_true',
            help='Проверить логи безопасности',
        )
        parser.add_argument(
            '--check-rate-limits',
            action='store_true',
            help='Проверить текущие rate limits',
        )
        parser.add_argument(
            '--clear-rate-limits',
            action='store_true',
            help='Очистить все rate limits',
        )
        parser.add_argument(
            '--summary',
            action='store_true',
            help='Показать краткую сводку безопасности',
        )
    
    def handle(self, *args, **options):
        if options['check_logs']:
            self.check_security_logs()
        elif options['check_rate_limits']:
            self.check_rate_limits()
        elif options['clear_rate_limits']:
            self.clear_rate_limits()
        elif options['summary']:
            self.show_security_summary()
        else:
            # По умолчанию показываем сводку
            self.show_security_summary()
    
    def check_security_logs(self):
        """Проверка логов безопасности"""
        log_file = 'logs/security.log'
        
        if not os.path.exists(log_file):
            self.stdout.write(
                self.style.WARNING('Файл логов безопасности не найден')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('=== Анализ логов безопасности ===')
        )
        
        # Читаем последние 100 строк лога
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:]
        
        # Анализируем логи
        security_events = defaultdict(int)
        ip_addresses = defaultdict(int)
        suspicious_patterns = defaultdict(int)
        
        for line in lines:
            if 'SECURITY_EVENT' in line:
                security_events['total'] += 1
                
                # Извлекаем IP адрес
                ip_match = re.search(r'IP: ([\d\.]+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    ip_addresses[ip] += 1
                
                # Анализируем паттерны
                if 'suspicious_request' in line:
                    suspicious_patterns['suspicious_request'] += 1
                elif 'rate_limit_exceeded' in line:
                    suspicious_patterns['rate_limit_exceeded'] += 1
        
        # Выводим статистику
        self.stdout.write(f"Всего событий безопасности: {security_events['total']}")
        self.stdout.write(f"Подозрительных запросов: {suspicious_patterns['suspicious_request']}")
        self.stdout.write(f"Превышений rate limit: {suspicious_patterns['rate_limit_exceeded']}")
        
        if ip_addresses:
            self.stdout.write("\nТоп IP адресов по активности:")
            sorted_ips = sorted(ip_addresses.items(), key=lambda x: x[1], reverse=True)
            for ip, count in sorted_ips[:5]:
                self.stdout.write(f"  {ip}: {count} событий")
    
    def check_rate_limits(self):
        """Проверка текущих rate limits"""
        self.stdout.write(
            self.style.SUCCESS('=== Текущие Rate Limits ===')
        )
        
        # Получаем все ключи rate limiting из кэша
        rate_limit_keys = []
        for key in cache._cache.keys():
            if key.startswith('rate_limit_'):
                rate_limit_keys.append(key)
        
        if not rate_limit_keys:
            self.stdout.write('Активных rate limits не найдено')
            return
        
        # Группируем по типу
        rate_limits = defaultdict(list)
        for key in rate_limit_keys:
            parts = key.split('_')
            if len(parts) >= 4:
                action_type = parts[2]
                ip = parts[3]
                count = cache.get(key, 0)
                rate_limits[action_type].append((ip, count))
        
        # Выводим статистику
        for action_type, limits in rate_limits.items():
            self.stdout.write(f"\n{action_type.upper()}:")
            for ip, count in limits:
                self.stdout.write(f"  {ip}: {count} запросов")
    
    def clear_rate_limits(self):
        """Очистка всех rate limits"""
        self.stdout.write(
            self.style.WARNING('Очистка всех rate limits...')
        )
        
        cleared_count = 0
        for key in list(cache._cache.keys()):
            if key.startswith('rate_limit_'):
                cache.delete(key)
                cleared_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Очищено {cleared_count} rate limits')
        )
    
    def show_security_summary(self):
        """Показать краткую сводку безопасности"""
        self.stdout.write(
            self.style.SUCCESS('=== Сводка безопасности 0123.ru ===')
        )
        
        # Проверяем настройки
        self.stdout.write(f"Rate limit загрузки: {getattr(settings, 'RATE_LIMIT_UPLOAD', 'не настроено')} запросов/мин")
        self.stdout.write(f"Rate limit API: {getattr(settings, 'RATE_LIMIT_API', 'не настроено')} запросов/мин")
        self.stdout.write(f"Окно времени: {getattr(settings, 'RATE_LIMIT_WINDOW', 'не настроено')} сек")
        
        # Проверяем логи
        log_file = 'logs/security.log'
        if os.path.exists(log_file):
            log_size = os.path.getsize(log_file)
            self.stdout.write(f"Размер логов безопасности: {log_size} байт")
        else:
            self.stdout.write(
                self.style.WARNING('Логи безопасности не настроены')
            )
        
        # Проверяем активные rate limits
        rate_limit_count = 0
        for key in cache._cache.keys():
            if key.startswith('rate_limit_'):
                rate_limit_count += 1
        
        self.stdout.write(f"Активных rate limits: {rate_limit_count}")
        
        # Рекомендации
        self.stdout.write("\n=== Рекомендации ===")
        if rate_limit_count > 0:
            self.stdout.write("✅ Rate limiting активен")
        else:
            self.stdout.write("⚠️  Rate limiting не активен")
        
        if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
            self.stdout.write("✅ Логирование безопасности настроено")
        else:
            self.stdout.write("⚠️  Логирование безопасности не настроено")
        
        self.stdout.write("\nИспользуйте --check-logs для анализа логов")
        self.stdout.write("Используйте --check-rate-limits для проверки rate limits")
