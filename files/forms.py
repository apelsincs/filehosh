from django import forms
from django.conf import settings
from .models import File
import os
from django.utils.translation import gettext_lazy as _


class FileUploadForm(forms.ModelForm):
    """
    Форма для загрузки файлов с поддержкой пароля и кастомного кода.
    """
    
    custom_code = forms.CharField(
        max_length=50,  # Увеличиваем максимальную длину
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введите желаемый код (необязательно)'),
            'title': _('Любые символы')
        }),
        help_text=_('Оставьте пустым для автоматической генерации')
    )
    
    password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введите пароль (необязательно)')
        }),
        help_text=_('Оставьте пустым для доступа без пароля')
    )
    
    is_protected = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label=_('Защитить паролем')
    )

    class Meta:
        model = File
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '*/*',
                'data-max-size': settings.MAX_FILE_SIZE
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].help_text = _('Максимальный размер: %(size)s МБ') % {
            'size': settings.MAX_FILE_SIZE // (1024*1024)
        }
    
    def clean_file(self):
        """Валидация загруженного файла"""
        file = self.cleaned_data.get('file')
        
        if not file:
            raise forms.ValidationError(_('Пожалуйста, выберите файл для загрузки.'))
        
        # Проверяем размер файла
        if file.size > settings.MAX_FILE_SIZE:
            max_size_mb = settings.MAX_FILE_SIZE // (1024 * 1024)
            raise forms.ValidationError(_('Размер файла не должен превышать %(size)s МБ.') % {'size': max_size_mb})

        return file
    
    def clean_custom_code(self):
        """Валидация кастомного кода"""
        custom_code = self.cleaned_data.get('custom_code')
        
        if custom_code:
            # Убираем все ограничения на символы и длину
            # Проверяем только уникальность
            if File.objects.filter(code=custom_code).exists():
                raise forms.ValidationError(_('Этот код уже используется. Выберите другой.'))
        
        return custom_code if custom_code else None
    
    def clean_password(self):
        """Валидация пароля"""
        password = self.cleaned_data.get('password')
        
        # Если установлен флаг защиты, требуем пароль
        wants_protection = self.data.get('is_protected') in ['on', 'true', '1']

        if wants_protection and not password:
            raise forms.ValidationError(_('Укажите пароль, если включена защита.'))
        
        # Убираем все ограничения на длину и сложность пароля
        return password


class PasswordForm(forms.Form):
    """
    Форма для ввода пароля при доступе к защищенному файлу.
    """
    
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введите пароль для доступа к файлу'),
            'autofocus': True
        }),
        label=_('Пароль')
    )
    
    def __init__(self, file_instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_instance = file_instance
    
    def clean_password(self):
        """Проверяет правильность пароля (поддержка старых незахешированных значений)"""
        from django.contrib.auth.hashers import check_password
        password = self.cleaned_data.get('password')
        
        if self.file_instance:
            stored = self.file_instance.password or ''
            is_hashed = stored.startswith('pbkdf2_') or stored.startswith('argon2') or stored.startswith('bcrypt')
            valid = check_password(password, stored) if is_hashed else (password == stored)
            if not valid:
                raise forms.ValidationError(_('Неверный пароль.'))
        
        return password


class FileEditForm(forms.ModelForm):
    """
    Форма для редактирования информации о файле.
    """
    
    new_code = forms.CharField(
        max_length=50,  # Увеличиваем максимальную длину
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введите новый код'),
            'title': _('Любые символы'),
            'id': 'newCode',
            'maxlength': '50'
        }),
        help_text=_('Оставьте пустым, чтобы не изменять')
    )
    
    new_password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Введите новый пароль')
        }),
        help_text=_('Оставьте пустым, чтобы убрать пароль')
    )
    
    class Meta:
        model = File
        fields = []
    
    def clean_new_code(self):
        """Валидация нового кода"""
        new_code = self.cleaned_data.get('new_code')
        
        if new_code:
            # Убираем все ограничения на символы и длину
            # Проверяем только уникальность, исключая текущий файл
            if File.objects.filter(code=new_code).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(_('Этот код уже используется. Выберите другой.'))
        
        return new_code if new_code else None 