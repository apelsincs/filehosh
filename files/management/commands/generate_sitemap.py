from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from files.models import File
from django.utils import timezone
import os


class Command(BaseCommand):
    help = 'Генерирует sitemap.xml файл'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='static/sitemap.xml',
            help='Путь для сохранения sitemap.xml файла'
        )

    def handle(self, *args, **options):
        output_path = options['output']
        
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Получаем домен
        try:
            site = Site.objects.get_current()
            domain = site.domain
        except Site.DoesNotExist:
            domain = '0123.ru'
        
        # Генерируем sitemap
        sitemap_content = self.generate_sitemap(domain)
        
        # Сохраняем файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
        
        self.stdout.write(
            self.style.SUCCESS(f'Sitemap успешно создан: {output_path}')
        )

    def generate_sitemap(self, domain):
        """Генерирует содержимое sitemap.xml"""
        
        # Начинаем XML
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        # Статические страницы
        static_pages = [
            ('', '1.0', 'daily'),  # Главная страница
            ('/files/recent/', '0.8', 'daily'),  # Мои файлы
        ]
        
        for url, priority, changefreq in static_pages:
            xml += f'  <url>\n'
            xml += f'    <loc>https://{domain}{url}</loc>\n'
            xml += f'    <changefreq>{changefreq}</changefreq>\n'
            xml += f'    <priority>{priority}</priority>\n'
            xml += f'  </url>\n'
        
        # Публичные файлы (без паролей)
        public_files = File.objects.filter(
            is_protected=False,
            expires_at__gt=timezone.now(),
            is_deleted=False
        ).order_by('-created_at')[:1000]  # Ограничиваем количество
        
        for file in public_files:
            xml += f'  <url>\n'
            xml += f'    <loc>https://{domain}/files/{file.code}/</loc>\n'
            xml += f'    <lastmod>{file.created_at.strftime("%Y-%m-%d")}</lastmod>\n'
            xml += f'    <changefreq>daily</changefreq>\n'
            xml += f'    <priority>0.6</priority>\n'
            xml += f'  </url>\n'
        
        # Закрываем XML
        xml += '</urlset>'
        
        return xml
