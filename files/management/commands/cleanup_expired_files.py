from django.core.management.base import BaseCommand
from django.utils import timezone
from files.models import File
import os


class Command(BaseCommand):
    help = 'Удаляет истекшие файлы'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет удалено без фактического удаления',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Находим истекшие файлы
        expired_files = File.objects.filter(
            expires_at__lt=timezone.now(),
            is_deleted=False
        )
        
        count = expired_files.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Нет истекших файлов для удаления')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'Будет удалено {count} истекших файлов:')
            )
            for file in expired_files:
                self.stdout.write(f'  - {file.filename} (код: {file.code}, истек: {file.expires_at})')
        else:
            # Удаляем файлы
            for file in expired_files:
                try:
                    # Удаляем физический файл
                    if file.file and os.path.exists(file.file.path):
                        os.remove(file.file.path)
                    
                    # Удаляем QR код
                    if file.qr_code and os.path.exists(file.qr_code.path):
                        os.remove(file.qr_code.path)
                    
                    # Помечаем как удаленный
                    file.is_deleted = True
                    file.save()
                    
                    self.stdout.write(f'Удален файл: {file.filename} (код: {file.code})')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Ошибка при удалении {file.filename}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Успешно удалено {count} истекших файлов')
            ) 