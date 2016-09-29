import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baseapp.settings')
from celery import Celery
from django.conf import settings


## configure Celery app instance singleton

app = Celery('{}_service'.format(settings.SERVICE_NAME))
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(settings.INSTALLED_APPS, related_name='tasks')

