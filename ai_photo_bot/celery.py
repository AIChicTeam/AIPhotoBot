import os
from celery import Celery

# Считываем переменную окружения с настройками Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_photo_bot.settings')

app = Celery('ai_photo_bot')

# Берём настройки из django settings с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим и регистрируем таски из всех приложений
app.autodiscover_tasks()
