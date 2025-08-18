from django.urls import path
from . import views

app_name = 'files'

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Поиск файлов
    path('search/', views.search_files, name='search_files'),
    
    # Последние файлы
    path('recent/', views.recent_files, name='recent_files'),
    
    # API для загрузки файлов
    path('api/upload/', views.api_upload, name='api_upload'),
    
    # Проверка доступности кода
    path('check-code/', views.check_code_availability, name='check_code_availability'),
    
    # Просмотр файла по коду
    path('<str:code>/', views.file_detail, name='file_detail'),
    
    # Скачивание файла
    path('<str:code>/download/', views.download_file, name='download_file'),
    
    # Редактирование файла
    path('<str:code>/edit/', views.edit_file, name='edit_file'),
    
    # Удаление файла
    path('<str:code>/delete/', views.delete_file, name='delete_file'),
] 