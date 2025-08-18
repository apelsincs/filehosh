from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    """
    Админка для управления файлами с расширенным функционалом.
    """
    
    list_display = [
        'code', 'filename', 'file_size_mb', 'is_protected', 
        'created_at', 'expires_at', 'download_count', 'status'
    ]
    
    list_filter = [
        'is_protected', 'created_at', 'expires_at'
    ]
    
    search_fields = ['code', 'filename', 'password']
    
    readonly_fields = [
        'code', 'file_size', 'created_at', 'download_count', 
        'last_downloaded', 'qr_code_preview'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('file', 'filename', 'code', 'file_size')
        }),
        ('Безопасность', {
            'fields': ('password', 'is_protected')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'expires_at', 'download_count', 'last_downloaded')
        }),
        ('QR код', {
            'fields': ('qr_code', 'qr_code_preview'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_mb(self, obj):
        """Отображает размер файла в МБ"""
        return f"{obj.get_file_size_mb()} МБ"
    file_size_mb.short_description = 'Размер (МБ)'
    file_size_mb.admin_order_field = 'file_size'
    
    def status(self, obj):
        """Отображает статус файла"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red; font-weight: bold;">Истек</span>'
            )
        else:
            remaining = obj.get_remaining_time()
            return format_html(
                '<span style="color: green; font-weight: bold;">Активен ({})</span>',
                remaining
            )
    status.short_description = 'Статус'
    
    def qr_code_preview(self, obj):
        """Предварительный просмотр QR кода"""
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 200px; height: auto;" />',
                obj.qr_code.url
            )
        return "QR код не сгенерирован"
    qr_code_preview.short_description = 'Предварительный просмотр QR кода'
    
    def get_queryset(self, request):
        """Оптимизированный queryset с предзагрузкой связанных данных"""
        return super().get_queryset(request).select_related()
    
    def save_model(self, request, obj, form, change):
        """Переопределяем сохранение для автоматической генерации QR кода"""
        if not change:  # Только при создании нового файла
            obj.filename = obj.file.name.split('/')[-1]
            obj.file_size = obj.file.size
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Переопределяем удаление для очистки файлов"""
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Переопределяем массовое удаление"""
        for obj in queryset:
            obj.delete()
    
    # Действия для админки
    actions = ['delete_expired_files', 'regenerate_qr_codes', 'extend_expiry']
    
    def delete_expired_files(self, request, queryset):
        """Удаляет истекшие файлы"""
        expired_count = 0
        for file_obj in queryset:
            if file_obj.is_expired():
                file_obj.delete()
                expired_count += 1
        
        self.message_user(
            request, 
            f'Удалено {expired_count} истекших файлов.'
        )
    delete_expired_files.short_description = 'Удалить истекшие файлы'
    
    def regenerate_qr_codes(self, request, queryset):
        """Перегенерирует QR коды для выбранных файлов"""
        regenerated_count = 0
        for file_obj in queryset:
            file_obj.generate_qr_code()
            file_obj.save()
            regenerated_count += 1
        
        self.message_user(
            request, 
            f'Перегенерировано {regenerated_count} QR кодов.'
        )
    regenerate_qr_codes.short_description = 'Перегенерировать QR коды'
    
    def extend_expiry(self, request, queryset):
        """Продлевает срок действия файлов на 24 часа"""
        extended_count = 0
        for file_obj in queryset:
            if not file_obj.is_expired():
                file_obj.expires_at = timezone.now() + timezone.timedelta(hours=24)
                file_obj.save()
                extended_count += 1
        
        self.message_user(
            request, 
            f'Продлен срок действия для {extended_count} файлов.'
        )
    extend_expiry.short_description = 'Продлить срок действия на 24 часа'
    
    # Настройки админки
    list_per_page = 25
    ordering = ['-created_at']
    
    # Фильтры по датам
    date_hierarchy = 'created_at'
    
    # Настройки для экспорта
    list_export = ['code', 'filename', 'file_size', 'created_at', 'expires_at', 'download_count']
    
    class Media:
        css = {
            'all': ('css/style.css',)
        }


# Настройки админки
admin.site.site_header = '0123.ru - Администрирование'
admin.site.site_title = '0123.ru'
admin.site.index_title = 'Панель управления файловым хостингом'
