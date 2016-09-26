import re
import os
from django.conf import settings
from django.contrib import admin
from django.conf.urls import url, include
from django.views.generic.base import RedirectView
from rest_framework import routers
from . import views

admin.autodiscover()

router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', admin.site.urls),

    url(r'^api/', include(router.urls)),
    url(r'^api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/session/check', views.session_check),
    url(r'^api/session/login', views.session_login),
    url(r'^api/session/logout', views.session_logout),

    url(r'^api/pictorlabs/', include('pictorlabs.urls')),

    url(r'^app/(?P<path>.*)$', views.serve_angular_app),
    url(r'^$', RedirectView.as_view(url='/app/', permanent=False), name='index'),
]
