"""
Функции для автоматического выполнения задач через cron
"""
import os
from django.utils import timezone
from files.models import File


def cleanup_expired_files():
    """
    Удаляет истекшие файлы.
    Эта функция вызывается автоматически через cron.
    """
    # Находим истекшие файлы
    expired_files = File.objects.filter(
        expires_at__lt=timezone.now(),
        is_deleted=False
    )
    
    count = expired_files.count()
    
    if count == 0:
        print(f"[{timezone.now()}] Нет истекших файлов для удаления")
        return
    
    print(f"[{timezone.now()}] Найдено {count} истекших файлов для удаления")
    
    # Удаляем файлы
    deleted_count = 0
    for file in expired_files:
        try:
            # Удаляем физический файл
            if file.file and os.path.exists(file.file.path):
                os.remove(file.file.path)
                print(f"Удален физический файл: {file.file.path}")
            
            # Удаляем QR код
            if file.qr_code and os.path.exists(file.qr_code.path):
                os.remove(file.qr_code.path)
                print(f"Удален QR код: {file.qr_code.path}")
            
            # Помечаем как удаленный
            file.is_deleted = True
            file.save()
            
            deleted_count += 1
            print(f"Удален файл: {file.filename} (код: {file.code})")
            
        except Exception as e:
            print(f"Ошибка при удалении {file.filename}: {e}")
    
    print(f"[{timezone.now()}] Успешно удалено {deleted_count} из {count} истекших файлов")
