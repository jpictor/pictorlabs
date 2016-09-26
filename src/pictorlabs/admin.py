from django.contrib import admin
from .models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'title', 'url', 'user', 'last_modified', 'created')
    list_filter = ('type', )

