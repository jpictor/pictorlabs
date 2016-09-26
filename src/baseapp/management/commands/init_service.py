from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Initialize the service...
    """

    def handle(self, *args, **options):
        print('nothing here yet...')