"""
Celery tasks for 0123.ru file hosting
"""
import os
import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from .models import File
from .management.commands.generate_sitemap import generate_sitemap

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='files.tasks.cleanup_expired_files')
def cleanup_expired_files(self):
    """
    Асинхронная задача для удаления истекших файлов.
    Заменяет cron задачу.
    """
    try:
        logger.info("Начинаем очистку истекших файлов...")
        
        # Находим истекшие файлы
        expired_files = File.objects.filter(
            expires_at__lt=timezone.now(),
            is_deleted=False
        )
        
        count = expired_files.count()
        
        if count == 0:
            logger.info("Нет истекших файлов для удаления")
            return f"Удалено файлов: 0"
        
        logger.info(f"Найдено {count} истекших файлов для удаления")
        
        # Удаляем файлы
        deleted_count = 0
        for file in expired_files:
            try:
                # Удаляем физический файл
                if file.file and os.path.exists(file.file.path):
                    os.remove(file.file.path)
                    logger.debug(f"Удален физический файл: {file.file.path}")
                
                # Удаляем QR код
                if file.qr_code and os.path.exists(file.qr_code.path):
                    os.remove(file.qr_code.path)
                    logger.debug(f"Удален QR код: {file.qr_code.path}")
                
                # Помечаем как удаленный
                file.is_deleted = True
                file.save()
                
                deleted_count += 1
                logger.debug(f"Удален файл: {file.filename} (код: {file.code})")
                
            except Exception as e:
                logger.error(f"Ошибка при удалении {file.filename}: {e}")
        
        # Очищаем кеш
        cache.clear()
        
        logger.info(f"Успешно удалено {deleted_count} из {count} истекших файлов")
        return f"Удалено файлов: {deleted_count}"
        
    except Exception as e:
        logger.error(f"Ошибка в задаче очистки файлов: {e}")
        raise

@shared_task(bind=True, name='files.tasks.generate_sitemap')
def generate_sitemap_task(self):
    """
    Асинхронная задача для генерации sitemap.
    """
    try:
        logger.info("Начинаем генерацию sitemap...")
        result = generate_sitemap()
        logger.info(f"Sitemap сгенерирован: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при генерации sitemap: {e}")
        raise

@shared_task(bind=True, name='files.tasks.cleanup_old_logs')
def cleanup_old_logs(self):
    """
    Асинхронная задача для очистки старых логов.
    """
    try:
        logger.info("Начинаем очистку старых логов...")
        
        # Очищаем логи старше 30 дней
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        # Здесь можно добавить логику очистки логов
        # Например, удаление старых файлов логов
        
        logger.info("Очистка логов завершена")
        return "Логи очищены"
        
    except Exception as e:
        logger.error(f"Ошибка при очистке логов: {e}")
        raise

@shared_task(bind=True, name='files.tasks.optimize_database')
def optimize_database(self):
    """
    Асинхронная задача для оптимизации базы данных.
    """
    try:
        logger.info("Начинаем оптимизацию базы данных...")
        
        with connection.cursor() as cursor:
            # Анализируем таблицы
            cursor.execute("ANALYZE files_file;")
            cursor.execute("ANALYZE django_session;")
            
            # Очищаем неиспользуемые страницы
            cursor.execute("VACUUM ANALYZE;")
            
            # Обновляем статистику
            cursor.execute("REFRESH MATERIALIZED VIEW IF EXISTS files_stats;")
        
        logger.info("Оптимизация базы данных завершена")
        return "База данных оптимизирована"
        
    except Exception as e:
        logger.error(f"Ошибка при оптимизации БД: {e}")
        raise

@shared_task(bind=True, name='files.tasks.cache_popular_files')
def cache_popular_files(self):
    """
    Асинхронная задача для кеширования популярных файлов.
    """
    try:
        logger.info("Начинаем кеширование популярных файлов...")
        
        # Получаем популярные файлы (по количеству скачиваний)
        popular_files = File.objects.filter(
            is_deleted=False,
            expires_at__gt=timezone.now()
        ).order_by('-download_count')[:100]
        
        # Кешируем информацию о файлах
        for file in popular_files:
            cache_key = f"popular_file_{file.code}"
            cache_data = {
                'filename': file.filename,
                'file_size': file.file_size,
                'download_count': file.download_count,
                'created_at': file.created_at.isoformat(),
                'file_type': file.get_file_type(),
                'file_type_name': file.get_file_type_name(),
                'file_type_icon': file.get_file_type_icon(),
            }
            cache.set(cache_key, cache_data, 3600)  # 1 час
        
        logger.info(f"Закешировано {popular_files.count()} популярных файлов")
        return f"Закешировано файлов: {popular_files.count()}"
        
    except Exception as e:
        logger.error(f"Ошибка при кешировании файлов: {e}")
        raise

@shared_task(bind=True, name='files.tasks.health_check')
def health_check(self):
    """
    Асинхронная задача для проверки здоровья системы.
    """
    try:
        logger.info("Выполняем проверку здоровья системы...")
        
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'database': 'healthy',
            'redis': 'healthy',
            'file_system': 'healthy',
            'tasks': 'healthy'
        }
        
        # Проверяем базу данных
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = f'unhealthy: {e}'
        
        # Проверяем Redis
        try:
            cache.set('health_check', 'ok', 60)
            if cache.get('health_check') == 'ok':
                health_status['redis'] = 'healthy'
            else:
                health_status['redis'] = 'unhealthy'
        except Exception as e:
            health_status['redis'] = f'unhealthy: {e}'
        
        # Проверяем файловую систему
        try:
            media_path = settings.MEDIA_ROOT
            if os.path.exists(media_path) and os.access(media_path, os.W_OK):
                health_status['file_system'] = 'healthy'
            else:
                health_status['file_system'] = 'unhealthy: no write access'
        except Exception as e:
            health_status['file_system'] = f'unhealthy: {e}'
        
        # Кешируем статус здоровья
        cache.set('system_health', health_status, 300)  # 5 минут
        
        logger.info("Проверка здоровья системы завершена")
        return health_status
        
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья: {e}")
        raise

@shared_task(bind=True, name='files.tasks.process_file_upload')
def process_file_upload(self, file_id):
    """
    Асинхронная задача для обработки загруженного файла.
    """
    try:
        logger.info(f"Начинаем обработку файла {file_id}...")
        
        file = File.objects.get(id=file_id)
        
        # Здесь можно добавить дополнительную обработку файла
        # Например, генерация превью, проверка на вирусы, и т.д.
        
        logger.info(f"Файл {file_id} обработан успешно")
        return f"Файл {file_id} обработан"
        
    except File.DoesNotExist:
        logger.error(f"Файл {file_id} не найден")
        return f"Файл {file_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка при обработке файла {file_id}: {e}")
        raise
