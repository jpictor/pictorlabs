from django.conf import settings


def service_settings(request):
    return {'SERVICE_VERSION': settings.SERVICE_VERSION}
