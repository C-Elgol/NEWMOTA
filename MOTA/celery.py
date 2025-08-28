# mota/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module for 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MOTA.settings')

# Create Celery app instance
app = Celery('mota_apps')

# Configure from Django settings with CELERY_ namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Default broker and backend (for Render free plan + Redis Key Value)
app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', app.conf.broker_url)

# Optional: serialization and timezone settings
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.timezone = os.environ.get('TZ', 'UTC')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Optional: debug task
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
