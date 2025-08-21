from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse, FileResponse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.urls import reverse
from django_ratelimit.decorators import ratelimit
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.shortcuts import get_current_site
import random
import string
from datetime import timedelta
import os

from .models import File
from .forms import FileUploadForm, PasswordForm, FileEditForm


def generate_unique_code():
    """
    Генерирует уникальный код для файла.
    Использует комбинацию букв и цифр для создания коротких кодов.
    """
    while True:
        # Генерируем код из 5 символов (буквы и цифры)
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        # Проверяем уникальность
        if not File.objects.filter(code=code).exists():
            return code


@ratelimit(key='ip', rate='10/m', method=['POST'])
def home(request):
    """
    Главная страница с формой загрузки файлов.
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            
            # Возвращаем ошибки валидации для AJAX запросов
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'non_field_errors': form.non_field_errors()
                })
        if form.is_valid():
            # Создаем новый файл
            file_instance = form.save(commit=False)
            
            # Устанавливаем имя файла и размер
            file_instance.filename = form.cleaned_data['file'].name
            file_instance.file_size = form.cleaned_data['file'].size
            
            # Генерируем или используем кастомный код
            custom_code = form.cleaned_data.get('custom_code')
            if custom_code:
                file_instance.code = custom_code
            else:
                file_instance.code = generate_unique_code()
            
            # Устанавливаем пароль и защиту
            password = form.cleaned_data.get('password')
            
            # Если есть пароль, то файл защищен
            if password:
                file_instance.password = make_password(password)
                file_instance.is_protected = True
            else:
                file_instance.is_protected = False
            
            # Связываем файл с анонимной сессией пользователя
            if hasattr(request, 'anonymous_session_id'):
                file_instance.session_id = request.anonymous_session_id
            
            # Устанавливаем время истечения (24 часа)
            file_instance.expires_at = timezone.now() + timedelta(hours=settings.FILE_EXPIRY_HOURS)
            
            # Сохраняем файл
            file_instance.save()
            
            # Возвращаем JSON ответ для показа модального окна
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Добавляем отладочную информацию
                response_data = {
                    'success': True,
                    'code': file_instance.code,
                    'url': request.build_absolute_uri(
                        reverse('files:file_detail', kwargs={'code': file_instance.code})
                    ),
                    'download_url': request.build_absolute_uri(
                        reverse('files:download_file', kwargs={'code': file_instance.code})
                    ),
                    'qr_url': request.build_absolute_uri(file_instance.qr_code.url) if file_instance.qr_code else None,
                    'expires_at': file_instance.expires_at.isoformat(),
                    'file_size': file_instance.file_size,
                    'filename': file_instance.filename,
                    'session_id': file_instance.session_id,
                    'is_protected': file_instance.is_protected,
                    'file_type': file_instance.get_file_type(),
                    'file_type_name': file_instance.get_file_type_name(),
                    'file_type_icon': file_instance.get_file_type_icon(),
                    'debug_info': {
                        'custom_code_provided': bool(custom_code),
                        'password_provided': bool(password),
                        'has_session': hasattr(request, 'anonymous_session_id'),
                        'session_id_value': getattr(request, 'anonymous_session_id', None)
                    }
                }
                return JsonResponse(response_data)
            
            # Для обычных запросов показываем сообщение и перенаправляем
            messages.success(request, f'Файл успешно загружен! Код: {file_instance.code}')
            return redirect('files:file_detail', code=file_instance.code)
    else:
        form = FileUploadForm()
    
    # Получаем последние загруженные файлы для отображения
    # Показываем только файлы текущего пользователя (если есть session_id)
    if hasattr(request, 'anonymous_session_id') and request.anonymous_session_id:
        recent_files = File.objects.filter(
            session_id=request.anonymous_session_id,
            expires_at__gt=timezone.now(),
            is_deleted=False
        ).order_by('-created_at')[:3]
    else:
        # Если session_id нет, показываем пустой список
        recent_files = []
    
    # Статистика для главной страницы
    total_files = File.objects.count()  # Все файлы (включая удаленные)
    total_downloads = File.objects.aggregate(Sum('download_count')).get('download_count__sum') or 0
    active_files = File.objects.filter(expires_at__gt=timezone.now(), is_deleted=False).count()
    protected_files = File.objects.filter(is_protected=True, expires_at__gt=timezone.now(), is_deleted=False).count()
    
    # Количество загруженных файлов за сегодня
    today = timezone.now().date()
    today_files = File.objects.filter(
        created_at__date=today
    ).count()

    context = {
        'form': form,
        'recent_files': recent_files,
        'max_file_size_mb': settings.MAX_FILE_SIZE // (1024 * 1024),
        'expiry_hours': settings.FILE_EXPIRY_HOURS,
        'total_files': total_files,
        'total_downloads': total_downloads,
        'active_files': active_files,
        'protected_files': protected_files,
        'today_files': today_files,
    }
    
    return render(request, 'files/home.html', context)


def file_detail(request, code):
    """
    Страница просмотра файла по коду.
    """
    file_instance = get_object_or_404(File, code=code.upper())
    
    # Проверяем, не удален ли файл
    if file_instance.is_deleted:
        raise Http404("Файл не найден")
    
    # Проверяем, не истек ли файл
    if file_instance.is_expired():
        messages.error(request, 'Файл истек и больше недоступен.')
        return redirect('files:home')
    
    # Если файл защищен паролем, всегда запрашиваем пароль
    if file_instance.is_protected:
        if request.method == 'POST':
            password_form = PasswordForm(file_instance, request.POST)
            if password_form.is_valid():
                # Пароль верный — показываем файл
                pass  # Продолжаем выполнение
            else:
                messages.error(request, 'Неверный пароль.')
                return render(request, 'files/password_required.html', {
                    'file': file_instance,
                    'form': password_form
                })
        else:
            # Всегда показываем форму пароля для защищенных файлов
            password_form = PasswordForm(file_instance)
            return render(request, 'files/password_required.html', {
                'file': file_instance,
                'form': password_form
            })
    
    # На странице деталей не изменяем счетчик скачиваний
    
    context = {
        'file': file_instance,
        'file_url': request.build_absolute_uri(reverse('files:file_detail', kwargs={'code': file_instance.code})),
    }
    
    return render(request, 'files/file_detail.html', context)


@ratelimit(key='ip', rate='20/m', method=['GET'])
def download_file(request, code):
    """
    Скачивание файла по коду.
    """
    file_instance = get_object_or_404(File, code=code.upper())
    
    # Проверяем, не удален ли файл
    if file_instance.is_deleted:
        raise Http404("Файл не найден")
    
    # Проверяем, не истек ли файл
    if file_instance.is_expired():
        raise Http404("Файл истек")
    
    # Если файл защищен паролем, проверяем пароль
    if file_instance.is_protected:
        password = request.GET.get('password')
        if not password:
            raise Http404("Файл защищен паролем. Укажите пароль в параметре ?password=...")
        
        from django.contrib.auth.hashers import check_password
        if not check_password(password, file_instance.password):
            raise Http404("Неверный пароль")
    
    # Увеличиваем счетчик скачиваний
    file_instance.increment_download_count()

    # Потоковая отдача файла
    file_stream = file_instance.file.open('rb')
    response = FileResponse(file_stream, as_attachment=True, filename=file_instance.filename)
    response['Content-Length'] = file_instance.file_size
    return response


def edit_file(request, code):
    """
    Редактирование информации о файле.
    """
    file_instance = get_object_or_404(File, code=code.upper())
    
    # Проверяем, не удален ли файл
    if file_instance.is_deleted:
        raise Http404("Файл не найден")
    
    # Проверяем, не истек ли файл
    if file_instance.is_expired():
        messages.error(request, 'Файл истек и больше недоступен для редактирования.')
        return redirect('files:home')
    
    if request.method == 'POST':
        form = FileEditForm(request.POST, instance=file_instance)
        if form.is_valid():
            # Обновляем код если указан новый
            new_code = form.cleaned_data.get('new_code')
            if new_code:
                file_instance.code = new_code
                file_instance.generate_qr_code()  # Перегенерируем QR код
            
            # Обновляем пароль
            new_password = form.cleaned_data.get('new_password')
            if new_password is not None:  # Пустая строка означает убрать пароль
                if new_password:
                    file_instance.password = make_password(new_password)
                    file_instance.is_protected = True
                else:
                    file_instance.password = None
                    file_instance.is_protected = False
            
            file_instance.save()
            messages.success(request, 'Информация о файле обновлена!')
            return redirect('files:file_detail', code=file_instance.code)
        else:
            # Возвращаем ошибки валидации для AJAX запросов
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors,
                    'non_field_errors': form.non_field_errors()
                })
    else:
        form = FileEditForm(instance=file_instance)
    
    context = {
        'file': file_instance,
        'form': form,
    }
    
    return render(request, 'files/edit_file.html', context)


def delete_file(request, code):
    """
    Удаление файла.
    """
    file_instance = get_object_or_404(File, code=code.upper())
    
    # Проверяем, не удален ли файл
    if file_instance.is_deleted:
        raise Http404("Файл не найден")
    
    # Проверяем, не истек ли файл
    if file_instance.is_expired():
        messages.error(request, 'Файл истек и больше недоступен для удаления.')
        return redirect('files:home')
    
    if request.method == 'POST':
        # Используем наш кастомный метод удаления
        file_instance.delete()
        messages.success(request, 'Файл успешно удален!')
        return redirect('files:home')
    
    context = {
        'file': file_instance,
    }
    
    return render(request, 'files/delete_file.html', context)


def check_code_availability(request):
    """
    Проверка доступности кода для файла.
    """
    code = request.GET.get('code', '').strip()
    
    if not code:
        return JsonResponse({'available': False, 'error': 'Код не указан'})
    
    # Проверяем, не занят ли код
    is_occupied = File.objects.filter(code=code).exists()
    
    return JsonResponse({
        'available': not is_occupied,
        'code': code,
        'occupied': is_occupied
    })


def search_files(request):
    """
    Поиск файлов по коду или имени.
    Показывает только файлы текущего пользователя.
    """
    query = request.GET.get('q', '').strip()
    
    if not query:
        return redirect('files:home')
    
    # Получаем только файлы текущего пользователя
    if hasattr(request, 'anonymous_session_id') and request.anonymous_session_id:
        # Ищем файлы по коду или имени только среди файлов пользователя
        files = File.objects.filter(
            Q(code__icontains=query) | Q(filename__icontains=query),
            session_id=request.anonymous_session_id,
            expires_at__gt=timezone.now(),
            is_deleted=False
        ).order_by('-created_at')
    else:
        # Если session_id нет, показываем пустой список
        files = File.objects.none()
    
    # Пагинация
    paginator = Paginator(files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'files_count': files.count(),
        'has_session': hasattr(request, 'anonymous_session_id') and request.anonymous_session_id,
    }
    
    return render(request, 'files/search_results.html', context)


def recent_files(request):
    """
    Страница с последними загруженными файлами.
    Показывает только файлы текущего пользователя.
    """
    # Получаем только файлы текущего пользователя
    if hasattr(request, 'anonymous_session_id') and request.anonymous_session_id:
        files = File.objects.filter(
            session_id=request.anonymous_session_id,
            expires_at__gt=timezone.now(),
            is_deleted=False
        ).order_by('-created_at')
        
        # Проверяем, есть ли активные файлы
        has_files = files.exists()
    else:
        # Если session_id нет, показываем пустой список
        files = File.objects.none()
        has_files = False
    
    # Пагинация только если есть файлы
    if has_files:
        paginator = Paginator(files, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
    
    context = {
        'page_obj': page_obj,
        'has_session': hasattr(request, 'anonymous_session_id') and request.anonymous_session_id,
        'has_files': has_files,
        'total_files': files.count() if has_files else 0,
    }
    
    return render(request, 'files/recent_files.html', context)


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='ip', rate='10/m', method=['POST'])
def api_upload(request):
    """
    API endpoint для загрузки файлов (для будущего развития).
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Создаем файл аналогично обычной загрузке
            file_instance = form.save(commit=False)
            file_instance.filename = form.cleaned_data['file'].name
            file_instance.file_size = form.cleaned_data['file'].size
            
            custom_code = form.cleaned_data.get('custom_code')
            if custom_code:
                file_instance.code = custom_code
            else:
                file_instance.code = generate_unique_code()
            
            password = form.cleaned_data.get('password')
            if password:
                file_instance.password = make_password(password)
                file_instance.is_protected = True
            
            # Связываем файл с анонимной сессией пользователя
            if hasattr(request, 'anonymous_session_id'):
                file_instance.session_id = request.anonymous_session_id
            
            file_instance.expires_at = timezone.now() + timedelta(hours=settings.FILE_EXPIRY_HOURS)
            file_instance.save()
            
            return JsonResponse({
                'success': True,
                'code': file_instance.code,
                'url': request.build_absolute_uri(
                    reverse('files:file_detail', kwargs={'code': file_instance.code})
                ),
                'download_url': request.build_absolute_uri(
                    reverse('files:download_file', kwargs={'code': file_instance.code})
                ),
                'qr_url': request.build_absolute_uri(file_instance.qr_code.url) if file_instance.qr_code else None,
                'expires_at': file_instance.expires_at.isoformat(),
                'file_size': file_instance.file_size,
                'filename': file_instance.filename,
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


# Sitemap классы
class StaticViewSitemap(Sitemap):
    """
    Sitemap для статических страниц сайта.
    """
    changefreq = 'daily'
    priority = 0.9
    
    def items(self):
        return ['files:home', 'files:recent_files']
    
    def location(self, item):
        return reverse(item)


class FileSitemap(Sitemap):
    """
    Sitemap для публичных файлов (без паролей).
    """
    changefreq = 'daily'
    priority = 0.7
    
    def items(self):
        # Возвращаем только публичные файлы (без паролей), которые не истекли
        return File.objects.filter(
            is_protected=False,
            expires_at__gt=timezone.now(),
            is_deleted=False
        ).order_by('-created_at')[:1000]  # Ограничиваем количество для производительности
    
    def lastmod(self, obj):
        return obj.created_at
    
    def location(self, obj):
        return reverse('files:file_detail', kwargs={'code': obj.code})


# Словарь sitemaps для urls.py
sitemaps = {
    'static': StaticViewSitemap,
    'files': FileSitemap,
}


def robots_txt(request):
    """
    Возвращает robots.txt файл.
    """
    from django.http import HttpResponse
    from django.template.loader import render_to_string
    
    content = render_to_string('robots.txt', {
        'domain': request.get_host(),
    })
    
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    """
    Возвращает sitemap.xml файл.
    """
    from django.http import HttpResponse
    from django.contrib.sites.models import Site
    
    try:
        site = Site.objects.get_current()
        domain = site.domain
    except Site.DoesNotExist:
        domain = '0123.ru'
    
    # Генерируем XML
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
    
    return HttpResponse(xml, content_type='application/xml')
