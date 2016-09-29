from django.conf.urls import url, include
from rest_framework import routers
from pictorlabs import views

router = routers.SimpleRouter()
router.register(r'entity', views.EntityViewSet, base_name='entity')

urlpatterns = [
    url(r'add_video[/]?$', views.add_video),
]

urlpatterns += router.urls
