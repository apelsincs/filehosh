"""
Celery configuration for 0123.ru file hosting
"""
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'filehost.settings_prod')

app = Celery('filehost')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Broker settings
    broker_url=os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0'),
    result_backend=os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    
    # Task routing
    task_routes={
        'files.tasks.*': {'queue': 'files'},
        'files.tasks.cleanup_expired_files': {'queue': 'maintenance'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'files': {
            'exchange': 'files',
            'routing_key': 'files',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'routing_key': 'maintenance',
        },
    },
    
    # Beat schedule (replaces cron)
    beat_schedule={
        'cleanup-expired-files': {
            'task': 'files.tasks.cleanup_expired_files',
            'schedule': 3600.0,  # Каждый час
        },
        'generate-sitemap': {
            'task': 'files.tasks.generate_sitemap',
            'schedule': 86400.0,  # Каждый день
        },
        'cleanup-old-logs': {
            'task': 'files.tasks.cleanup_old_logs',
            'schedule': 604800.0,  # Каждую неделю
        },
    },
    
    # Result backend settings
    result_expires=3600,  # Результаты хранятся 1 час
    
    # Security
    worker_disable_rate_limits=False,
    task_annotations={
        '*': {
            'rate_limit': '100/m',  # 100 задач в минуту
        }
    }
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
