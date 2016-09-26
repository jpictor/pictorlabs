from .celery_ext import app
from .logging_ext import logger
import django.db


@app.task(name='baseapp.healthcheck_task', bind=True)
def healthcheck_task(self):
    """
    Healthcheck task, test connections to all services.
    """
    healthy = True
    msgs = []

    ## check MYSQL database
    try:
        cursor = django.db.connection.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        msgs.append('sql_db=OK')
    except Exception:
        msgs.append('sql_db=FAILED')
        healthy = False

    ## create health check log response
    msg = 'healthcheck: %s' % ','.join(msgs)
    if healthy:
        logger.info(msg)
    else:
        logger.error(msg)
