## configure logging
import logging
import logging.config
from django.conf import settings
logging.config.fileConfig(settings.LOGGING_CONFIG_FILE)

## configure Celery system
from . import celery_ext

logging.getLogger().setLevel(settings.LOG_LEVEL)
logging.debug('logging system configured for appname=%s using %s' % (settings.APPNAME, settings.LOGGING_CONFIG_FILE))
