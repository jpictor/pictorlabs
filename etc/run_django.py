import os
import sys
from django.core import management
if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == 'runserver':
        sys.argv.append(os.environ['SERVICE_PORT'])
        sys.argv.append('--nothreading')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baseapp.settings")
    management.execute_from_command_line()
